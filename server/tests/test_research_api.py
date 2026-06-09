import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from schemas.research import DegradedMode, InputKind, TopicCandidate, WebMaterial
from services.session_store import ResearchSessionStore, research_store


@pytest.mark.asyncio
async def test_research_api_empty_content(client):
    response = await client.post("/api/v1/questions/research", json={"content": "   "})
    assert response.status_code == 400


async def _poll_research_until_done(client, task_id: str):
    for _ in range(20):
        response = await client.get(f"/api/v1/questions/research/{task_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "done":
            return payload
        if payload["status"] == "failed":
            pytest.fail(payload.get("error_message") or "research task failed")
        await asyncio.sleep(0.05)
    pytest.fail("research task did not finish in time")


@pytest.mark.asyncio
async def test_research_api_mock_mode(client):
    with patch("services.research.research_service.use_mock_tavily", return_value=True):
        with patch(
            "services.research.research_service.run_research_agent",
            new=AsyncMock(
                return_value=(
                    [
                        WebMaterial(
                            source="search",
                            title="Harness Engineering",
                            url="https://example.com",
                            content="AI harness methodology",
                            score=0.9,
                        )
                    ],
                    DegradedMode.none,
                    1,
                )
            ),
        ):
            with patch(
                "services.research.research_service.build_topic_candidate_chain"
            ) as mock_chain_builder:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.return_value = type(
                    "R",
                    (),
                    {
                        "candidates": [
                            TopicCandidate(
                                id="harness-ai",
                                title="AI Harness Engineering",
                                summary="AI 工程方法论",
                                source_urls=["https://example.com"],
                            )
                        ]
                    },
                )()
                mock_chain_builder.return_value = mock_chain
                create_response = await client.post(
                    "/api/v1/questions/research",
                    json={"content": "Harness Engineering"},
                )

    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]
    data = (await _poll_research_until_done(client, task_id))["result"]
    assert data["research_session_id"]
    assert len(data["candidates"]) >= 1
    assert data["input_kind"] == "keyword"
    assert data["mock_mode"] is True


@pytest.mark.asyncio
async def test_research_api_degraded_response_fields(client):
    with patch("services.research.research_service.use_mock_tavily", return_value=True):
        with patch(
            "services.research.research_service.run_research_agent",
            new=AsyncMock(
                return_value=(
                    [],
                    DegradedMode.no_web_results,
                    1,
                )
            ),
        ):
            create_response = await client.post(
                "/api/v1/questions/research",
                json={"content": "obscure topic"},
            )

    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]
    data = (await _poll_research_until_done(client, task_id))["result"]
    assert data["degraded_mode"] == "no_web_results"
    assert data["degraded_message"]


@pytest.mark.asyncio
async def test_research_session_used_by_generate(client, sample_knowledge, sample_question_set):
    research_store.create(
        research_session_id="rs-1",
        user_content="Harness Engineering",
        materials=[
            WebMaterial(
                source="search",
                title="Harness Engineering",
                url="https://example.com",
                content="AI harness methodology with enough content",
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
        "services.generation_task_service.run_question_pipeline",
        new=AsyncMock(
            return_value=("sid-grounded", sample_knowledge, sample_question_set, False, True)
        ),
    ) as mock_pipeline:
        create_response = await client.post(
            "/api/v1/questions/generate",
            json={
                "content": "Harness Engineering",
                "questions_per_level": 5,
                "research_session_id": "rs-1",
                "selected_topic_id": "harness-ai",
            },
        )

    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]
    poll_payload = None
    for _ in range(20):
        poll_response = await client.get(f"/api/v1/questions/generate/{task_id}")
        poll_payload = poll_response.json()
        if poll_payload["status"] == "done":
            break
        await asyncio.sleep(0.05)
    assert poll_payload is not None
    assert poll_payload["status"] == "done"
    assert poll_payload["result"]["grounded"] is True
    assert mock_pipeline.await_args.kwargs["research_snapshot"] is not None


@pytest.mark.asyncio
async def test_research_session_expired(client):
    store = ResearchSessionStore(ttl_seconds=1)
    with patch("services.research.research_service.research_store", store):
        store.create(
            research_session_id="expired-id",
            user_content="test",
            materials=[],
            candidates=[
                TopicCandidate(
                    id="user-input",
                    title="test",
                    summary="s",
                    source_urls=[],
                )
            ],
            input_kind=InputKind.keyword,
            degraded_mode=DegradedMode.none,
            mock_mode=True,
        )
        store._sessions["expired-id"].created_at = __import__("time").time() - 10
        response = await client.post(
            "/api/v1/questions/generate",
            json={
                "content": "test",
                "questions_per_level": 3,
                "research_session_id": "expired-id",
                "selected_topic_id": "user-input",
            },
        )
    assert response.status_code == 410


def test_research_store_ttl():
    store = ResearchSessionStore(ttl_seconds=1)
    store.create(
        research_session_id="rid",
        user_content="x",
        materials=[],
        candidates=[],
        input_kind=InputKind.keyword,
        degraded_mode=DegradedMode.none,
        mock_mode=True,
    )
    store._sessions["rid"].created_at = __import__("time").time() - 5
    assert store.get("rid") is None


def test_topic_candidate_truncates_long_fields():
    candidate = TopicCandidate(
        id="prompt-engineering",
        title="Prompt Engineering、Context Engineering、Harness Engineering 三层递进关系" * 2,
        summary="x" * 250,
        source_urls=[],
    )
    assert len(candidate.title) == 60
    assert len(candidate.summary) == 200
