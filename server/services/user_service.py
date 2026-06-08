from sqlalchemy.orm import Session

from db.models.user import User
from services.exp_config import exp_progress, level_for_exp
from services.quiz_record_service import compute_user_quiz_stats


def build_user_stats(db: Session, user: User) -> dict[str, float | int]:
    return compute_user_quiz_stats(db, user)


def serialize_user(user: User, db: Session | None = None) -> dict:
    current_in_level, required, _ = exp_progress(user.exp)
    level, title = level_for_exp(user.exp)
    stats = build_user_stats(db, user) if db is not None else {
        "total_quizzes": user.total_quizzes,
        "average_accuracy": 0.0,
        "wrong_question_count": 0,
        "weekly_quiz_count": 0,
    }
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatarUrl": user.avatar_url,
        "exp": user.exp,
        "level": level,
        "title": title,
        "totalQuizzes": user.total_quizzes,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "expProgress": {
            "current": current_in_level,
            "required": required,
            "totalExp": user.exp,
        },
        "stats": {
            "totalQuizzes": stats["total_quizzes"],
            "averageAccuracy": stats["average_accuracy"],
            "wrongQuestionCount": stats["wrong_question_count"],
            "weeklyQuizCount": stats["weekly_quiz_count"],
        },
    }


def update_user_profile(db: Session, user: User, nickname: str | None, avatar_url: str | None) -> User:
    if nickname is not None:
        cleaned = nickname.strip()
        if not cleaned:
            raise ValueError("昵称不能为空")
        if len(cleaned) > 64:
            raise ValueError("昵称过长")
        user.nickname = cleaned

    if avatar_url is not None:
        cleaned = avatar_url.strip()
        if len(cleaned) > 512:
            raise ValueError("头像地址过长")
        user.avatar_url = cleaned

    level, title = level_for_exp(user.exp)
    user.level = level
    user.title = title
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
