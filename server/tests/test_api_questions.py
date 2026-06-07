from unittest.mock import AsyncMock, patch

import pytest

from schemas.knowledge import StructuredKnowledge
from schemas.question import QuestionSet
from services.question_pipeline import (
    build_generate_response,
    check_answer,
    compute_report_stats,
    find_question,
    normalize_content,
)
from services.session_store import session_store


def test_normalize_content_empty_raises():
    with pytest.raises(Exception) as exc:
        normalize_content("   ")
    assert exc.value.status_code == 400


def test_normalize_content_truncates_long_text():
    text, truncated = normalize_content("a" * 4500)
    assert truncated is True
    assert len(text) == 4000


def test_check_answer_single_and_multiple(sample_question_set):
    q1 = sample_question_set.levels[0].questions[0]
    assert check_answer(q1, ["A"]) is True
    assert check_answer(q1, ["B"]) is False


def test_find_question_from_session(sample_knowledge, sample_question_set):
    session_store.create("sid", "text", sample_knowledge, sample_question_set)
    question = find_question("sid", "q1")
    assert question.id == "q1"


def test_build_generate_response_hides_answers(sample_knowledge, sample_question_set):
    response = build_generate_response("sid", sample_knowledge, sample_question_set, False)
    payload = response.model_dump()
    assert "answer" not in str(payload)
    assert response.levels[0].questions[0].stem.startswith("Go")


def test_compute_report_stats():
    from schemas.report import AnswerRecord

    answers = [
        AnswerRecord(question_id="q1", user_answer=["A"], is_correct=True, time_spent=1000),
        AnswerRecord(question_id="q2", user_answer=["B"], is_correct=False, time_spent=2000),
    ]
    accuracy, total, correct, wrong, duration = compute_report_stats(answers)
    assert total == 2
    assert correct == 1
    assert wrong == 1
    assert accuracy == 50.0
    assert duration == 3


@pytest.mark.asyncio
async def test_generate_questions_api(client, sample_knowledge, sample_question_set):
    with patch(
        "routers.questions.run_question_pipeline",
        new=AsyncMock(
            return_value=("sid-1", sample_knowledge, sample_question_set, False)
        ),
    ):
        response = await client.post(
            "/api/v1/questions/generate",
            json={"content": "Go 并发", "questions_per_level": 5},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sid-1"
    assert data["topic"] == sample_knowledge.topic
    assert "answer" not in str(data)


@pytest.mark.asyncio
async def test_generate_questions_empty_content(client):
    response = await client.post(
        "/api/v1/questions/generate",
        json={"content": "   ", "questions_per_level": 5},
    )
    assert response.status_code == 400
