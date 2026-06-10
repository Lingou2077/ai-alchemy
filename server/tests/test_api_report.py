from unittest.mock import AsyncMock, patch

import pytest

from schemas.report import AnswerRecord, ConceptNode, ReportData, WeakPoint
from services.session_store import session_store


@pytest.mark.asyncio
async def test_generate_report_api(client, sample_knowledge, sample_question_set):
    session_store.create("sid-1", "text", sample_knowledge, sample_question_set)
    fake_report = ReportData(
        sessionId="sid-1",
        topic=sample_knowledge.topic,
        accuracy=50.0,
        totalQuestions=2,
        correctCount=1,
        wrongCount=1,
        duration=3,
        weakPoints=[WeakPoint(name="channel", reason="答错")],
        summary="总结",
        suggestion="建议",
        shareTagline="channel 待精炼",
        conceptMastery=[
            ConceptNode(name="goroutine", mastery="partial", relatedQuestionCount=1)
        ],
    )

    with patch(
        "routers.report.run_report_pipeline",
        new=AsyncMock(return_value=fake_report),
    ):
        response = await client.post(
            "/api/v1/report/generate",
            json={
                "session_id": "sid-1",
                "answers": [
                    {
                        "question_id": "q1",
                        "user_answer": ["A"],
                        "is_correct": True,
                        "time_spent": 1200,
                    },
                    {
                        "question_id": "q2",
                        "user_answer": ["F"],
                        "is_correct": False,
                        "time_spent": 1800,
                    },
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "总结"
    assert data["shareTagline"]
    assert data["weakPoints"][0]["name"] == "channel"


@pytest.mark.asyncio
async def test_generate_report_missing_session(client):
    response = await client.post(
        "/api/v1/report/generate",
        json={"session_id": "missing", "answers": []},
    )
    assert response.status_code == 404
