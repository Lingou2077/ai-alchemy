from sqlalchemy.orm import Session

from db.models.exp_log import ExpLog
from db.models.user import User
from services.exp_config import level_for_exp


EXP_QUIZ_COMPLETE = 10
EXP_QUIZ_SUCCESS_BONUS = 5


def get_exp_log_by_session(db: Session, session_id: str) -> ExpLog | None:
    return db.query(ExpLog).filter(ExpLog.session_id == session_id).one_or_none()


def settle_exp(db: Session, user: User, session_id: str, quiz_status: str) -> dict:
    """同一 session 仅结算一次，返回 expGain 结构。"""
    existing = get_exp_log_by_session(db, session_id)
    if existing is not None:
        return {
            "amount": existing.amount,
            "leveledUp": existing.level_after > existing.level_before,
            "newLevel": existing.level_after,
            "newTitle": level_for_exp(existing.exp_after)[1],
            "levelBefore": existing.level_before,
        }

    amount = EXP_QUIZ_COMPLETE
    if quiz_status == "completed":
        amount += EXP_QUIZ_SUCCESS_BONUS

    exp_before = user.exp
    level_before, _ = level_for_exp(exp_before)
    exp_after = exp_before + amount
    level_after, title_after = level_for_exp(exp_after)

    log = ExpLog(
        user_id=user.id,
        session_id=session_id,
        amount=amount,
        reason="quiz_complete" if quiz_status != "completed" else "quiz_complete+success",
        exp_before=exp_before,
        exp_after=exp_after,
        level_before=level_before,
        level_after=level_after,
    )
    db.add(log)

    user.exp = exp_after
    user.level = level_after
    user.title = title_after
    db.add(user)
    db.flush()

    return {
        "amount": amount,
        "leveledUp": level_after > level_before,
        "newLevel": level_after,
        "newTitle": title_after,
        "levelBefore": level_before,
    }
