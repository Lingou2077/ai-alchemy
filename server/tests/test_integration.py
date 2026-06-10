import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from schemas.report import ConceptNode, ReportData
from services.session_store import session_store


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_end_to_end_quiz_flow(client, sample_knowledge, sample_question_set):
    fake_report = ReportData(
        sessionId="sid-flow",
        topic=sample_knowledge.topic,
        accuracy=100.0,
        totalQuestions=2,
        correctCount=2,
        wrongCount=0,
        duration=5,
        weakPoints=[],
        summary="通关总结",
        suggestion="继续练习",
        shareTagline="炼金成功！",
        conceptMastery=[
            ConceptNode(name="goroutine", mastery="mastered", relatedQuestionCount=1)
        ],
    )

    async def fake_question_pipeline(content, count, **kwargs):
        session_store.create("sid-flow", content, sample_knowledge, sample_question_set)
        return ("sid-flow", sample_knowledge, sample_question_set, False, False)

    with patch(
        "services.generation_task_service.run_question_pipeline",
        new=AsyncMock(side_effect=fake_question_pipeline),
    ), patch(
        "routers.report.run_report_pipeline",
        new=AsyncMock(return_value=fake_report),
    ):
        create = await client.post(
            "/api/v1/questions/generate",
            json={"content": "Go 并发内容", "questions_per_level": 5},
        )
        assert create.status_code == 200
        task_id = create.json()["task_id"]

        session_id = None
        for _ in range(20):
            poll = await client.get(f"/api/v1/questions/generate/{task_id}")
            payload = poll.json()
            if payload["status"] == "done":
                session_id = payload["result"]["session_id"]
                break
            await asyncio.sleep(0.05)
        assert session_id == "sid-flow"

        check = await client.post(
            "/api/v1/answers/check",
            json={
                "session_id": session_id,
                "question_id": "q1",
                "user_answer": ["A"],
            },
        )
        assert check.status_code == 200
        assert check.json()["is_correct"] is True

        report = await client.post(
            "/api/v1/report/generate",
            json={
                "session_id": session_id,
                "answers": [
                    {
                        "question_id": "q1",
                        "user_answer": ["A"],
                        "is_correct": True,
                        "time_spent": 1000,
                    }
                ],
            },
        )
        assert report.status_code == 200
        assert report.json()["summary"] == "通关总结"
