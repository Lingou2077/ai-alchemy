import json
import time
import uuid

from fastapi import HTTPException

from chains.topic_candidate_chain import build_topic_candidate_chain
from schemas.research import (
    DegradedMode,
    InputKind,
    ResearchResponse,
    TopicCandidate,
    WebMaterial,
)
from services.research.input_classifier import classify_input
from services.research.materials import (
    apply_materials_fallback,
    degraded_user_message,
    fallback_text_material,
)
from services.research.context_budget import format_materials_for_prompt
from services.research.research_agent import run_research_agent
from services.research.tavily_tool_factory import use_mock_tavily
from config import settings
from services.content_utils import normalize_content
from services.session_store import research_store


def _materials_to_text(materials: list[WebMaterial]) -> str:
    return format_materials_for_prompt(
        materials,
        settings.topic_candidate_materials_budget,
        include_source_in_title=True,
        url_line_prefix="URL",
        empty_text="（无联网材料）",
    )


def _synthetic_candidate(user_content: str) -> TopicCandidate:
    title = user_content.strip()[:60] or "用户输入的内容"
    return TopicCandidate(
        id="user-input",
        title=title,
        summary="基于您提供的内容",
        source_urls=[],
    )


async def _build_candidates(
    user_content: str,
    materials: list[WebMaterial],
    degraded_mode: DegradedMode,
) -> list[TopicCandidate]:
    if degraded_mode in {DegradedMode.no_web_results, DegradedMode.agent_timeout}:
        return [_synthetic_candidate(user_content)]

    chain = build_topic_candidate_chain()
    result = await chain.ainvoke(
        {
            "user_content": user_content,
            "materials_text": _materials_to_text(materials),
        }
    )
    if result is None:
        return [_synthetic_candidate(user_content)]
    candidates = (result.candidates or [])[:3]
    if candidates:
        return candidates
    return [_synthetic_candidate(user_content)]


async def run_research(content: str) -> ResearchResponse:
    normalized_content, _ = normalize_content(content)
    input_kind = classify_input(normalized_content)

    materials, degraded_mode, _ = await run_research_agent(normalized_content, input_kind)
    materials, degraded_mode = apply_materials_fallback(materials, normalized_content, degraded_mode)

    candidates = await _build_candidates(normalized_content, materials, degraded_mode)
    research_session_id = str(uuid.uuid4())
    research_store.create(
        research_session_id=research_session_id,
        user_content=normalized_content,
        materials=materials,
        candidates=candidates,
        input_kind=input_kind,
        degraded_mode=degraded_mode,
        mock_mode=use_mock_tavily(),
    )

    return ResearchResponse(
        research_session_id=research_session_id,
        candidates=candidates,
        input_kind=input_kind,
        degraded_mode=degraded_mode,
        mock_mode=use_mock_tavily(),
        degraded_message=degraded_user_message(degraded_mode),
    )


def get_research_session_or_410(research_session_id: str):
    session = research_store.get(research_session_id)
    if session is None:
        raise HTTPException(status_code=410, detail="检索会话已过期，请重新联网检索")
    return session
