from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies import get_optional_user
from db.models.user import User
from schemas.question import GenerateQuestionsRequest
from schemas.task import GenerateTaskStatusResponse, TaskCreatedResponse
from services.generation_task_service import create_generate_task, get_generate_task_status

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


@router.post("/generate", response_model=TaskCreatedResponse)
async def create_generate_questions_task(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> TaskCreatedResponse:
    return create_generate_task(db, request, user_id=current_user.id if current_user else None)


@router.get("/generate/{task_id}", response_model=GenerateTaskStatusResponse)
async def get_generate_questions_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> GenerateTaskStatusResponse:
    return get_generate_task_status(db, task_id)
