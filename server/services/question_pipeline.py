import logging
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException

from chains.knowledge_chain import build_knowledge_chain
from chains.question_chain import build_question_chain
from chains.report_chain import build_report_chain
from schemas.knowledge import StructuredKnowledge
from schemas.question import (
    GenerateQuestionsResponse,
    LevelPublic,
    Question,
    QuestionPublic,
    QuestionSet,
)
from schemas.report import AnswerRecord, GenerateReportRequest, ReportData, ReportLLMOutput
from schemas.research import EXPLORE_ALL_TOPIC_ID, TopicCandidate, WebMaterial
from schemas.task import ResearchSessionSnapshot, TaskStep
from services.grounding import (
    assemble_explore_all_document,
    assemble_focused_document,
    collect_grounding_sources,
    resolve_grounding_mode,
)
from services.research.research_service import get_research_session_or_410
from services.content_utils import normalize_content
from services.report_sanitize import sanitize_report_llm_output
from services.session_store import session_store
from services.share_tagline import resolve_share_tagline

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 2
StepCallback = Callable[[TaskStep, str], None]


def _step_failure_detail(step_name: str) -> str:
    if step_name == "知识解析":
        return "知识解析失败，请精简内容后重试"
    return f"{step_name}失败，请重试"


def find_question(session_id: str, question_id: str) -> Question:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    for level in session.questions.levels:
        for question in level.questions:
            if question.id == question_id:
                return question
    raise HTTPException(status_code=404, detail="题目不存在")


def check_answer(question: Question, user_answer: list[str]) -> bool:
    normalized_user = sorted({answer.strip().upper() for answer in user_answer if answer.strip()})
    normalized_correct = sorted({answer.strip().upper() for answer in question.answer})
    return normalized_user == normalized_correct


async def invoke_with_retry(chain, payload: dict[str, Any], step_name: str):
    last_error: Exception | None = None
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            result = await chain.ainvoke(payload)
            if result is not None:
                return result
            logger.warning("%s returned None (attempt %d/%d)", step_name, attempt, _RETRY_ATTEMPTS)
        except Exception as exc:  # noqa: BLE001 - retry boundary
            last_error = exc
            logger.warning(
                "%s raised %s (attempt %d/%d): %s",
                step_name,
                type(exc).__name__,
                attempt,
                _RETRY_ATTEMPTS,
                exc,
            )
    raise HTTPException(status_code=503, detail=_step_failure_detail(step_name)) from last_error


async def run_question_pipeline(
    content: str,
    count: int,
    *,
    research_session_id: str | None = None,
    selected_topic_id: str | None = None,
    research_snapshot: dict[str, Any] | None = None,
    on_step: StepCallback | None = None,
) -> tuple[str, StructuredKnowledge, QuestionSet, bool, bool]:
    normalized_content, truncated = normalize_content(content)
    grounded = False
    grounding_document = normalized_content
    grounding_mode: str | None = None
    grounding_sources: list[str] = []
    stored_research_session_id: str | None = None
    stored_selected_topic_id: str | None = None

    knowledge_prompt = "knowledge.txt"
    question_prompt = "question.txt"
    knowledge_payload = {"content": normalized_content}

    if research_snapshot or (research_session_id and selected_topic_id):
        if research_snapshot:
            snapshot = ResearchSessionSnapshot.model_validate(research_snapshot)
            materials = [WebMaterial.model_validate(item) for item in snapshot.materials]
            candidates = [TopicCandidate.model_validate(item) for item in snapshot.candidates]
            stored_research_session_id = snapshot.research_session_id
        else:
            research_session = get_research_session_or_410(research_session_id or "")
            materials = research_session.materials
            candidates = research_session.candidates
            stored_research_session_id = research_session_id

        candidate_map = {item.id: item for item in candidates}
        grounding_mode = resolve_grounding_mode(selected_topic_id or "")
        grounded = True
        stored_selected_topic_id = selected_topic_id
        grounding_sources = collect_grounding_sources(materials)

        if selected_topic_id == EXPLORE_ALL_TOPIC_ID:
            grounding_document = assemble_explore_all_document(
                normalized_content,
                candidates,
                materials,
            )
            knowledge_prompt = "knowledge_explore.txt"
            question_prompt = "question_explore.txt"
            topic_hint = normalized_content[:40]
            knowledge_payload = {
                "content": grounding_document,
                "topic_hint": topic_hint,
            }
        else:
            candidate = candidate_map.get(selected_topic_id or "")
            if candidate is None:
                raise HTTPException(status_code=422, detail="所选主题无效，请重新确认")
            grounding_document = assemble_focused_document(
                normalized_content,
                candidate,
                materials,
            )
            knowledge_prompt = "knowledge_grounded.txt"
            knowledge_payload = {"content": grounding_document}

    if knowledge_prompt == "knowledge_explore.txt":
        knowledge_chain = build_knowledge_chain(
            prompt_file=knowledge_prompt,
            human_template="Grounding 材料：\n{content}\n\n主题提示：{topic_hint}",
        )
    elif grounded:
        knowledge_chain = build_knowledge_chain(
            prompt_file=knowledge_prompt,
            human_template="Grounding 材料：\n{content}",
        )
    else:
        knowledge_chain = build_knowledge_chain()

    question_chain = build_question_chain(prompt_file=question_prompt)

    if on_step:
        on_step(TaskStep.knowledge, "正在解析知识…")
    knowledge = await invoke_with_retry(
        knowledge_chain,
        knowledge_payload,
        "知识解析",
    )
    if on_step:
        on_step(TaskStep.questions, "正在生成题目…")
    questions = await invoke_with_retry(
        question_chain,
        {
            "structured_knowledge": knowledge.model_dump_json(ensure_ascii=False),
            "count": count,
        },
        "出题",
    )

    session_id = str(uuid.uuid4())
    session_store.create(
        session_id,
        normalized_content,
        knowledge,
        questions,
        research_session_id=stored_research_session_id,
        selected_topic_id=stored_selected_topic_id,
        grounding_mode=grounding_mode,
        grounding_sources=grounding_sources,
        web_research_enabled=grounded,
    )
    return session_id, knowledge, questions, truncated, grounded


def build_generate_response(
    session_id: str,
    knowledge: StructuredKnowledge,
    questions: QuestionSet,
    truncated: bool,
    grounded: bool = False,
) -> GenerateQuestionsResponse:
    public_levels = [
        LevelPublic(
            level_index=level.level_index,
            questions=[QuestionPublic.from_question(q) for q in level.questions],
        )
        for level in questions.levels
    ]
    return GenerateQuestionsResponse(
        session_id=session_id,
        topic=knowledge.topic,
        levels=public_levels,
        truncated=truncated,
        grounded=grounded,
    )


def build_answers_detail(answers: list[AnswerRecord]) -> str:
    lines = []
    for item in answers:
        status = "正确" if item.is_correct else "错误"
        lines.append(
            f"- 题目 {item.question_id}: 用户答案 {item.user_answer}，结果 {status}，用时 {item.time_spent}ms"
        )
    return "\n".join(lines) if lines else "无答题记录"


def compute_report_stats(answers: list[AnswerRecord]) -> tuple[float, int, int, int, int]:
    total = len(answers)
    correct = sum(1 for item in answers if item.is_correct)
    wrong = total - correct
    duration_ms = sum(item.time_spent for item in answers)
    duration_seconds = max(1, duration_ms // 1000)
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    return accuracy, total, correct, wrong, duration_seconds


async def run_report_pipeline(request: GenerateReportRequest) -> ReportData:
    session = session_store.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    accuracy, total, correct, wrong, duration = compute_report_stats(request.answers)
    if request.duration_sec is not None and request.duration_sec > 0:
        duration = request.duration_sec
    report_chain = build_report_chain()
    raw: ReportLLMOutput = await invoke_with_retry(
        report_chain,
        {
            "structured_knowledge": session.knowledge.model_dump_json(ensure_ascii=False),
            "answers_detail": build_answers_detail(request.answers),
            "accuracy": accuracy,
            "duration": duration,
            "session_id": request.session_id,
            "topic": session.knowledge.topic,
        },
        "报告生成",
    )
    raw = sanitize_report_llm_output(raw)

    report = ReportData(
        sessionId=request.session_id,
        topic=session.knowledge.topic,
        accuracy=accuracy,
        totalQuestions=total,
        correctCount=correct,
        wrongCount=wrong,
        duration=duration,
        weakPoints=raw.weak_points,
        summary=raw.summary,
        suggestion=raw.suggestion,
        shareTagline="",
        conceptMastery=raw.concept_mastery,
    )
    report.share_tagline = resolve_share_tagline(
        raw.share_tagline,
        topic=session.knowledge.topic,
        quiz_status=request.quiz_status,
        accuracy=accuracy,
    )
    return report
