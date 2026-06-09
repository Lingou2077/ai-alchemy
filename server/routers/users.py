from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from config import settings
from db.models.user import User
from db.session import get_db
from dependencies import get_current_user
from schemas.user import UpdateUserRequest, UserPublic, UserStats
from schemas.user_data import (
    QuizHistoryDetail,
    QuizHistoryListResponse,
    WrongQuestionDetail,
    WrongQuestionListResponse,
)
from services.avatar_service import build_public_avatar_url, save_avatar_file
from services.quiz_record_service import (
    delete_quiz_record,
    get_quiz_record_for_user,
    list_quiz_history,
    serialize_quiz_history_detail,
    serialize_quiz_history_item,
)
from services.user_service import build_user_stats, serialize_user, update_user_profile
from services.wrong_question_service import (
    get_wrong_question_for_user,
    list_wrong_questions,
    serialize_wrong_question_detail,
    serialize_wrong_question_item,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserPublic, response_model_by_alias=True)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    return UserPublic.model_validate(serialize_user(current_user, db))


@router.patch("/me", response_model=UserPublic, response_model_by_alias=True)
async def patch_me(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    if request.nickname is None and request.avatar_url is None:
        raise HTTPException(status_code=400, detail="请提供要更新的字段")
    try:
        user = update_user_profile(db, current_user, request.nickname, request.avatar_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserPublic.model_validate(serialize_user(user, db))


@router.get("/me/stats", response_model=UserStats, response_model_by_alias=True)
async def get_me_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStats:
    stats = build_user_stats(db, current_user)
    return UserStats.model_validate(
        {
            "totalQuizzes": stats["total_quizzes"],
            "averageAccuracy": stats["average_accuracy"],
            "wrongQuestionCount": stats["wrong_question_count"],
            "weeklyQuizCount": stats["weekly_quiz_count"],
        }
    )


@router.get("/me/history", response_model=QuizHistoryListResponse, response_model_by_alias=True)
async def get_me_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizHistoryListResponse:
    items, total = list_quiz_history(db, current_user.id, page, limit)
    return QuizHistoryListResponse(
        items=[serialize_quiz_history_item(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/me/history/{session_id}", response_model=QuizHistoryDetail, response_model_by_alias=True)
async def get_me_history_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizHistoryDetail:
    record = get_quiz_record_for_user(db, current_user.id, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return QuizHistoryDetail.model_validate(serialize_quiz_history_detail(record))


@router.delete("/me/history/{session_id}", status_code=204)
async def delete_me_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_quiz_record(db, current_user.id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="历史记录不存在")


@router.post("/me/avatar", response_model=UserPublic, response_model_by_alias=True)
async def upload_me_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    try:
        relative_path = save_avatar_file(current_user.id, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    base_url = settings.public_base_url.strip() or str(request.base_url).rstrip("/")
    avatar_url = build_public_avatar_url(relative_path, base_url)
    user = update_user_profile(db, current_user, None, avatar_url)
    return UserPublic.model_validate(serialize_user(user, db))


@router.get("/me/wrong-questions", response_model=WrongQuestionListResponse, response_model_by_alias=True)
async def get_me_wrong_questions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WrongQuestionListResponse:
    items, total = list_wrong_questions(db, current_user.id, page, limit)
    return WrongQuestionListResponse(
        items=[serialize_wrong_question_item(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get(
    "/me/wrong-questions/{record_id}",
    response_model=WrongQuestionDetail,
    response_model_by_alias=True,
)
async def get_me_wrong_question_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WrongQuestionDetail:
    record = get_wrong_question_for_user(db, current_user.id, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    return WrongQuestionDetail.model_validate(serialize_wrong_question_detail(record))
