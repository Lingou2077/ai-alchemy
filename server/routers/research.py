from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models.user import User
from db.session import get_db
from dependencies import get_optional_user
from schemas.research import ResearchRequest
from schemas.task import ResearchTaskStatusResponse, TaskCreatedResponse
from services.generation_task_service import create_research_task, get_research_task_status

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


@router.post("/research", response_model=TaskCreatedResponse)
async def create_research_topics_task(
    request: ResearchRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> TaskCreatedResponse:
    return create_research_task(db, request.content, user_id=current_user.id if current_user else None)


@router.get("/research/{task_id}", response_model=ResearchTaskStatusResponse)
async def get_research_topics_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> ResearchTaskStatusResponse:
    return get_research_task_status(db, task_id)
