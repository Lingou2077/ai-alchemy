import pytest

from services.session_store import session_store


@pytest.mark.asyncio
async def test_check_answer_api(client, sample_knowledge, sample_question_set):
    session_store.create("sid-1", "text", sample_knowledge, sample_question_set)

    correct = await client.post(
        "/api/v1/answers/check",
        json={"session_id": "sid-1", "question_id": "q1", "user_answer": ["A"]},
    )
    assert correct.status_code == 200
    assert correct.json()["is_correct"] is True
    assert correct.json()["correct_answer"] == ["A"]

    wrong = await client.post(
        "/api/v1/answers/check",
        json={"session_id": "sid-1", "question_id": "q1", "user_answer": ["B"]},
    )
    assert wrong.status_code == 200
    assert wrong.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_check_answer_missing_session(client):
    response = await client.post(
        "/api/v1/answers/check",
        json={"session_id": "missing", "question_id": "q1", "user_answer": ["A"]},
    )
    assert response.status_code == 404
