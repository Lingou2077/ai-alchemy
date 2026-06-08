from datetime import datetime

from sqlalchemy.orm import Session

from db.models.user import User
from db.models.wrong_question import WrongQuestion


def upsert_wrong_question(
    db: Session,
    user: User,
    question_id: str,
    session_id: str,
    topic: str,
    stem: str,
    options: list[dict],
    correct_answer: list[str],
    explanation: str,
    difficulty: str,
    last_wrong_at: datetime,
) -> WrongQuestion:
    existing = (
        db.query(WrongQuestion)
        .filter(WrongQuestion.user_id == user.id, WrongQuestion.question_id == question_id)
        .one_or_none()
    )
    if existing is not None:
        existing.wrong_count += 1
        existing.last_wrong_at = last_wrong_at
        existing.session_id = session_id
        existing.topic = topic
        existing.stem = stem
        existing.options = options
        existing.correct_answer = correct_answer
        existing.explanation = explanation
        existing.difficulty = difficulty
        db.add(existing)
        db.flush()
        return existing

    record = WrongQuestion(
        user_id=user.id,
        question_id=question_id,
        session_id=session_id,
        topic=topic,
        stem=stem,
        options=options,
        correct_answer=correct_answer,
        explanation=explanation,
        difficulty=difficulty,
        wrong_count=1,
        last_wrong_at=last_wrong_at,
    )
    db.add(record)
    db.flush()
    return record


def list_wrong_questions(db: Session, user_id: int, page: int = 1, limit: int = 20) -> tuple[list[WrongQuestion], int]:
    page = max(1, page)
    limit = min(max(1, limit), 50)
    query = db.query(WrongQuestion).filter(WrongQuestion.user_id == user_id)
    total = query.count()
    items = (
        query.order_by(WrongQuestion.last_wrong_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def get_wrong_question_for_user(db: Session, user_id: int, record_id: int) -> WrongQuestion | None:
    return (
        db.query(WrongQuestion)
        .filter(WrongQuestion.user_id == user_id, WrongQuestion.id == record_id)
        .one_or_none()
    )


def serialize_wrong_question_item(record: WrongQuestion) -> dict:
    return {
        "id": record.id,
        "questionId": record.question_id,
        "topic": record.topic,
        "stem": record.stem,
        "difficulty": record.difficulty,
        "wrongCount": record.wrong_count,
        "lastWrongAt": record.last_wrong_at.isoformat() if record.last_wrong_at else None,
    }


def serialize_wrong_question_detail(record: WrongQuestion) -> dict:
    return {
        **serialize_wrong_question_item(record),
        "options": record.options,
        "correctAnswer": record.correct_answer,
        "explanation": record.explanation,
    }
