from datetime import datetime

from sqlalchemy.orm import Session

from db.models.user import User
from schemas.report import ExpGainResponse, GenerateReportRequest, ReportData, ReportStatsResponse
from services.exp_service import get_exp_log_by_session, settle_exp
from services.quiz_record_service import (
    build_report_stats,
    create_quiz_record,
    get_quiz_record_by_session,
    sync_wrong_questions_from_session,
)
from services.session_store import session_store


def sync_quiz_result(
    db: Session,
    user: User,
    request: GenerateReportRequest,
    report: ReportData,
) -> tuple[ExpGainResponse | None, ReportStatsResponse | None]:
    session = session_store.get(request.session_id)
    if session is None:
        raise ValueError("会话不存在")

    quiz_status = request.quiz_status or "completed"
    duration_sec = request.duration_sec if request.duration_sec is not None else report.duration
    now = datetime.now()

    existing = get_quiz_record_by_session(db, request.session_id)
    if existing is not None:
        exp_log = get_exp_log_by_session(db, request.session_id)
        exp_gain = None
        if exp_log is not None:
            from services.exp_config import level_for_exp

            exp_gain = ExpGainResponse(
                amount=exp_log.amount,
                leveledUp=exp_log.level_after > exp_log.level_before,
                newLevel=exp_log.level_after,
                newTitle=level_for_exp(exp_log.exp_after)[1],
                levelBefore=exp_log.level_before,
            )
        stats = ReportStatsResponse.model_validate(build_report_stats(db, user.id, existing))
        return exp_gain, stats

    record = create_quiz_record(
        db=db,
        user=user,
        session_id=request.session_id,
        report=report,
        quiz_status=quiz_status,
        duration_sec=duration_sec,
        finished_at=now,
    )
    sync_wrong_questions_from_session(db, user, session, request.answers, now=now)

    user.total_quizzes += 1
    db.add(user)

    exp_result = settle_exp(db, user, request.session_id, quiz_status)
    exp_gain = ExpGainResponse.model_validate(exp_result)
    stats = ReportStatsResponse.model_validate(build_report_stats(db, user.id, record))

    db.flush()
    db.refresh(user)
    return exp_gain, stats
