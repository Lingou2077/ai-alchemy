from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from schemas.report import ConceptNode, ReportData, WeakPoint
from services.session_store import session_store


async def login(client: AsyncClient, code: str = "mock-quiz-user") -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_fake_report(session_id: str, topic: str, accuracy: float = 80.0) -> ReportData:
    return ReportData(
        sessionId=session_id,
        topic=topic,
        accuracy=accuracy,
        totalQuestions=2,
        correctCount=1 if accuracy < 100 else 2,
        wrongCount=1 if accuracy < 100 else 0,
        duration=120,
        weakPoints=[WeakPoint(name="goroutine", reason="答错")],
        summary="总结内容",
        suggestion="建议内容",
        conceptMastery=[ConceptNode(name="goroutine", mastery="partial", relatedQuestionCount=1)],
    )


async def post_report(
    client: AsyncClient,
    session_id: str,
    token: str | None = None,
    quiz_status: str = "completed",
    answers: list[dict] | None = None,
) -> dict:
    payload = {
        "session_id": session_id,
        "answers": answers
        or [
            {"question_id": "q1", "user_answer": ["A"], "is_correct": True, "time_spent": 1000},
            {"question_id": "q2", "user_answer": ["F"], "is_correct": False, "time_spent": 2000},
        ],
        "quiz_status": quiz_status,
        "duration_sec": 120,
    }
    headers = auth_headers(token) if token else {}
    fake_report = make_fake_report(session_id, "Go 并发编程基础", 50.0 if quiz_status == "failed" else 80.0)

    with patch("routers.report.run_report_pipeline", new=AsyncMock(return_value=fake_report)):
        response = await client.post("/api/v1/report/generate", json=payload, headers=headers)
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_report_sync_creates_quiz_record(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-sync-1", "text", sample_knowledge, sample_question_set)
    token = await login(client, "mock-sync-1")

    body = await post_report(client, "sid-sync-1", token, quiz_status="completed")
    assert body["expGain"]["amount"] == 15
    assert body["stats"]["weeklyQuizIndex"] == 1

    history = await client.get("/api/v1/users/me/history", headers=auth_headers(token))
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["topic"] == "Go 并发编程基础"


@pytest.mark.asyncio
async def test_report_sync_is_idempotent(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-idem", "text", sample_knowledge, sample_question_set)
    token = await login(client, "mock-idem")

    await post_report(client, "sid-idem", token)
    await post_report(client, "sid-idem", token)

    history = await client.get("/api/v1/users/me/history", headers=auth_headers(token))
    assert history.json()["total"] == 1

    me = await client.get("/api/v1/users/me", headers=auth_headers(token))
    assert me.json()["exp"] == 15
    assert me.json()["totalQuizzes"] == 1


@pytest.mark.asyncio
async def test_failed_quiz_grants_base_exp_only(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-fail", "text", sample_knowledge, sample_question_set)
    token = await login(client, "mock-fail-exp")

    body = await post_report(client, "sid-fail", token, quiz_status="failed")
    assert body["expGain"]["amount"] == 10


@pytest.mark.asyncio
async def test_wrong_questions_collected(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-wrong", "text", sample_knowledge, sample_question_set)
    token = await login(client, "mock-wrong")

    await post_report(client, "sid-wrong", token)

    wrong = await client.get("/api/v1/users/me/wrong-questions", headers=auth_headers(token))
    assert wrong.status_code == 200
    assert wrong.json()["total"] == 1
    assert wrong.json()["items"][0]["questionId"] == "q2"


@pytest.mark.asyncio
async def test_wrong_question_dedup_increments_count(client: AsyncClient, sample_knowledge, sample_question_set):
    token = await login(client, "mock-wrong-dedup")

    session_store.create("sid-w1", "text", sample_knowledge, sample_question_set)
    await post_report(client, "sid-w1", token)

    session_store.create("sid-w2", "text", sample_knowledge, sample_question_set)
    await post_report(client, "sid-w2", token)

    wrong = await client.get("/api/v1/users/me/wrong-questions", headers=auth_headers(token))
    assert wrong.json()["total"] == 1
    assert wrong.json()["items"][0]["wrongCount"] == 2


@pytest.mark.asyncio
async def test_history_isolated_between_users(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-iso", "text", sample_knowledge, sample_question_set)
    token_a = await login(client, "mock-hist-a")
    token_b = await login(client, "mock-hist-b")

    await post_report(client, "sid-iso", token_a)

    detail = await client.get("/api/v1/users/me/history/sid-iso", headers=auth_headers(token_b))
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_history_detail_returns_summary(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-detail", "text", sample_knowledge, sample_question_set)
    token = await login(client, "mock-detail")

    await post_report(client, "sid-detail", token)

    detail = await client.get("/api/v1/users/me/history/sid-detail", headers=auth_headers(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["summary"] == "总结内容"
    assert body["accuracy"] == 80.0


@pytest.mark.asyncio
async def test_stats_reflect_quiz_records(client: AsyncClient, sample_knowledge, sample_question_set):
    token = await login(client, "mock-stats")

    session_store.create("sid-st1", "text", sample_knowledge, sample_question_set)
    await post_report(client, "sid-st1", token, quiz_status="completed")

    session_store.create("sid-st2", "text", sample_knowledge, sample_question_set)
    await post_report(client, "sid-st2", token, quiz_status="failed")

    stats = await client.get("/api/v1/users/me/stats", headers=auth_headers(token))
    assert stats.status_code == 200
    body = stats.json()
    assert body["totalQuizzes"] == 2
    assert body["averageAccuracy"] == 65.0
    assert body["wrongQuestionCount"] == 1


@pytest.mark.asyncio
async def test_compare_last_accuracy(client: AsyncClient, sample_knowledge, sample_question_set):
    token = await login(client, "mock-compare")

    session_store.create("sid-c1", "text", sample_knowledge, sample_question_set)
    await post_report(client, "sid-c1", token, quiz_status="failed")

    session_store.create("sid-c2", "text", sample_knowledge, sample_question_set)
    body = await post_report(client, "sid-c2", token, quiz_status="completed")
    assert body["stats"]["compareLastAccuracy"] == 30.0


@pytest.mark.asyncio
async def test_unauthenticated_report_skips_sync(client: AsyncClient, sample_knowledge, sample_question_set):
    session_store.create("sid-anon", "text", sample_knowledge, sample_question_set)
    body = await post_report(client, "sid-anon", token=None)
    assert body.get("expGain") is None
    assert body.get("stats") is None
