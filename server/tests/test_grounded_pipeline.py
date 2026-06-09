import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from schemas.knowledge import StructuredKnowledge
from schemas.question import QuestionSet
from schemas.research import DegradedMode, InputKind, TopicCandidate, WebMaterial
from services.grounding import assemble_explore_all_document, assemble_focused_document
from services.session_store import research_store


async def _poll_generate_until_done(client, task_id: str):
    for _ in range(20):
        response = await client.get(f"/api/v1/questions/generate/{task_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "done":
            return payload["result"]
        if payload["status"] == "failed":
            pytest.fail(payload.get("error_message") or "generate task failed")
        await asyncio.sleep(0.05)
    pytest.fail("generate task did not finish in time")


def test_assemble_focused_document():
    doc = assemble_focused_document(
        "Harness Engineering",
        TopicCandidate(
            id="harness-ai",
            title="AI Harness",
            summary="AI 工程",
            source_urls=["https://example.com"],
        ),
        [
            WebMaterial(
                source="search",
                title="Article",
                url="https://example.com",
                content="details",
                score=0.8,
            )
        ],
    )
    assert "Harness Engineering" in doc
    assert "AI Harness" in doc


def test_assemble_explore_all_document():
    doc = assemble_explore_all_document(
        "Harness Engineering",
        [
            TopicCandidate(id="a", title="A", summary="sa", source_urls=[]),
            TopicCandidate(id="b", title="B", summary="sb", source_urls=[]),
        ],
        [],
    )
    assert "方向 1" in doc
    assert "方向 2" in doc


@pytest.mark.asyncio
async def test_grounded_generate_focused(client, sample_knowledge, sample_question_set):
    research_store.create(
        research_session_id="rs-1",
        user_content="Harness Engineering",
        materials=[
            WebMaterial(
                source="search",
                title="Harness",
                url="https://example.com",
                content="AI harness engineering methodology",
                score=0.9,
            )
        ],
        candidates=[
            TopicCandidate(
                id="harness-ai",
                title="AI Harness Engineering",
                summary="AI 工程方法论",
                source_urls=["https://example.com"],
            )
        ],
        input_kind=InputKind.keyword,
        degraded_mode=DegradedMode.none,
        mock_mode=True,
    )
    with patch(
        "services.question_pipeline.invoke_with_retry",
        new=AsyncMock(side_effect=[sample_knowledge, sample_question_set]),
    ):
        create_response = await client.post(
            "/api/v1/questions/generate",
            json={
                "content": "Harness Engineering",
                "questions_per_level": 3,
                "research_session_id": "rs-1",
                "selected_topic_id": "harness-ai",
            },
        )
    assert create_response.status_code == 200
    result = await _poll_generate_until_done(client, create_response.json()["task_id"])
    assert result["grounded"] is True


@pytest.mark.asyncio
async def test_grounded_generate_explore_all(client, sample_knowledge, sample_question_set):
    research_store.create(
        research_session_id="rs-2",
        user_content="Harness Engineering",
        materials=[
            WebMaterial(
                source="search",
                title="Harness",
                url="https://example.com",
                content="overview",
                score=0.8,
            )
        ],
        candidates=[
            TopicCandidate(id="a", title="A", summary="sa", source_urls=[]),
            TopicCandidate(id="b", title="B", summary="sb", source_urls=[]),
        ],
        input_kind=InputKind.keyword,
        degraded_mode=DegradedMode.none,
        mock_mode=True,
    )
    with patch(
        "services.question_pipeline.invoke_with_retry",
        new=AsyncMock(side_effect=[sample_knowledge, sample_question_set]),
    ):
        create_response = await client.post(
            "/api/v1/questions/generate",
            json={
                "content": "Harness Engineering",
                "questions_per_level": 3,
                "research_session_id": "rs-2",
                "selected_topic_id": "__all__",
            },
        )
    assert create_response.status_code == 200
    result = await _poll_generate_until_done(client, create_response.json()["task_id"])
    assert result["grounded"] is True


@pytest.mark.asyncio
async def test_grounded_generate_degraded_materials(client, sample_knowledge, sample_question_set):
    research_store.create(
        research_session_id="rs-degraded",
        user_content="冷门主题 XYZ",
        materials=[
            WebMaterial(
                source="text",
                title="用户输入",
                url="",
                content="冷门主题 XYZ",
                score=None,
            )
        ],
        candidates=[
            TopicCandidate(
                id="user-input",
                title="冷门主题 XYZ",
                summary="基于您提供的内容",
                source_urls=[],
            )
        ],
        input_kind=InputKind.keyword,
        degraded_mode=DegradedMode.no_web_results,
        mock_mode=True,
    )
    with patch(
        "services.question_pipeline.invoke_with_retry",
        new=AsyncMock(side_effect=[sample_knowledge, sample_question_set]),
    ):
        create_response = await client.post(
            "/api/v1/questions/generate",
            json={
                "content": "冷门主题 XYZ",
                "questions_per_level": 3,
                "research_session_id": "rs-degraded",
                "selected_topic_id": "user-input",
            },
        )
    assert create_response.status_code == 200
    result = await _poll_generate_until_done(client, create_response.json()["task_id"])
    assert result["grounded"] is True


@pytest.mark.asyncio
async def test_generate_without_research_regression(client, sample_knowledge, sample_question_set):
    with patch(
        "services.generation_task_service.run_question_pipeline",
        new=AsyncMock(return_value=("sid-legacy", sample_knowledge, sample_question_set, False, False)),
    ):
        create_response = await client.post(
            "/api/v1/questions/generate",
            json={"content": "Go 并发", "questions_per_level": 5},
        )
    assert create_response.status_code == 200
    result = await _poll_generate_until_done(client, create_response.json()["task_id"])
    assert result["grounded"] is False
