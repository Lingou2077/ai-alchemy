from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models.quiz_record import QuizRecord
from db.models.user import User
from db.models.wrong_question import WrongQuestion
from schemas.report import AnswerRecord, ReportData
from services.session_store import SessionData


def _week_start(now: datetime) -> datetime:
    """自然周：周一 00:00 起算。"""
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start - timedelta(days=start.weekday())


def get_quiz_record_by_session(db: Session, session_id: str) -> QuizRecord | None:
    return db.query(QuizRecord).filter(QuizRecord.session_id == session_id).one_or_none()


def get_quiz_record_for_user(db: Session, user_id: int, session_id: str) -> QuizRecord | None:
    return (
        db.query(QuizRecord)
        .filter(QuizRecord.user_id == user_id, QuizRecord.session_id == session_id)
        .one_or_none()
    )


def create_quiz_record(
    db: Session,
    user: User,
    session_id: str,
    report: ReportData,
    quiz_status: str,
    duration_sec: int,
    finished_at: datetime | None = None,
) -> QuizRecord:
    existing = get_quiz_record_by_session(db, session_id)
    if existing is not None:
        return existing

    record = QuizRecord(
        user_id=user.id,
        session_id=session_id,
        topic=report.topic,
        accuracy=Decimal(str(round(report.accuracy, 2))),
        question_count=report.total_questions,
        duration_sec=duration_sec,
        status=quiz_status,
        summary=report.summary,
        suggestion=report.suggestion,
        weak_points=[item.model_dump(by_alias=True) for item in report.weak_points],
        finished_at=finished_at or datetime.now(),
    )
    db.add(record)
    db.flush()
    return record


def list_quiz_history(db: Session, user_id: int, page: int = 1, limit: int = 20) -> tuple[list[QuizRecord], int]:
    page = max(1, page)
    limit = min(max(1, limit), 50)
    query = db.query(QuizRecord).filter(QuizRecord.user_id == user_id)
    total = query.count()
    items = (
        query.order_by(QuizRecord.finished_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def serialize_quiz_history_item(record: QuizRecord) -> dict:
    return {
        "sessionId": record.session_id,
        "topic": record.topic,
        "accuracy": float(record.accuracy),
        "questionCount": record.question_count,
        "durationSec": record.duration_sec,
        "status": record.status,
        "finishedAt": record.finished_at.isoformat() if record.finished_at else None,
    }


def serialize_quiz_history_detail(record: QuizRecord) -> dict:
    return {
        **serialize_quiz_history_item(record),
        "summary": record.summary,
        "suggestion": record.suggestion,
        "weakPoints": record.weak_points or [],
    }


def compute_user_quiz_stats(db: Session, user: User) -> dict[str, float | int]:
    avg_result = (
        db.query(func.avg(QuizRecord.accuracy))
        .filter(QuizRecord.user_id == user.id)
        .scalar()
    )
    week_start = _week_start(datetime.now())
    weekly_count = (
        db.query(func.count(QuizRecord.id))
        .filter(QuizRecord.user_id == user.id, QuizRecord.finished_at >= week_start)
        .scalar()
    ) or 0
    wrong_count = db.query(func.count(WrongQuestion.id)).filter(WrongQuestion.user_id == user.id).scalar() or 0
    return {
        "total_quizzes": user.total_quizzes,
        "average_accuracy": round(float(avg_result or 0), 1),
        "wrong_question_count": int(wrong_count),
        "weekly_quiz_count": int(weekly_count),
    }


def get_previous_record(db: Session, user_id: int, before: datetime, exclude_session_id: str) -> QuizRecord | None:
    return (
        db.query(QuizRecord)
        .filter(
            QuizRecord.user_id == user_id,
            QuizRecord.finished_at < before,
            QuizRecord.session_id != exclude_session_id,
        )
        .order_by(QuizRecord.finished_at.desc())
        .first()
    )


def get_related_history(
    db: Session,
    user_id: int,
    topic: str,
    exclude_session_id: str,
    limit: int = 3,
) -> list[QuizRecord]:
    return (
        db.query(QuizRecord)
        .filter(
            QuizRecord.user_id == user_id,
            QuizRecord.topic == topic,
            QuizRecord.session_id != exclude_session_id,
        )
        .order_by(QuizRecord.finished_at.desc())
        .limit(limit)
        .all()
    )


def build_report_stats(db: Session, user_id: int, current: QuizRecord) -> dict:
    previous = get_previous_record(db, user_id, current.finished_at, current.session_id)
    compare_last: float | None = None
    if previous is not None:
        compare_last = round(float(current.accuracy) - float(previous.accuracy), 1)

    week_start = _week_start(current.finished_at)
    weekly_index = (
        db.query(func.count(QuizRecord.id))
        .filter(
            QuizRecord.user_id == user_id,
            QuizRecord.finished_at >= week_start,
            QuizRecord.finished_at <= current.finished_at,
        )
        .scalar()
    ) or 1

    related = get_related_history(db, user_id, current.topic, current.session_id)
    return {
        "compareLastAccuracy": compare_last,
        "weeklyQuizIndex": int(weekly_index),
        "relatedHistory": [serialize_quiz_history_item(item) for item in related],
    }


def sync_wrong_questions_from_session(
    db: Session,
    user: User,
    session: SessionData,
    answers: list[AnswerRecord],
    now: datetime | None = None,
) -> None:
    from services.wrong_question_service import upsert_wrong_question

    now = now or datetime.now()
    topic = session.knowledge.topic
    question_map = {
        question.id: question
        for level in session.questions.levels
        for question in level.questions
    }

    for answer in answers:
        if answer.is_correct:
            continue
        question = question_map.get(answer.question_id)
        if question is None:
            continue
        upsert_wrong_question(
            db=db,
            user=user,
            question_id=question.id,
            session_id=session.session_id,
            topic=topic,
            stem=question.stem,
            options=[{"key": opt.key, "text": opt.text} for opt in question.options],
            correct_answer=question.answer,
            explanation=question.explanation,
            difficulty=question.difficulty,
            last_wrong_at=now,
        )
