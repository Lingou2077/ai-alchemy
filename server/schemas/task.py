from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.question import GenerateQuestionsResponse
from schemas.research import ResearchResponse


class TaskType(str, Enum):
    research = "research"
    generate = "generate"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class TaskStep(str, Enum):
    pending = "pending"
    research = "research"
    topic_candidates = "topic_candidates"
    knowledge = "knowledge"
    questions = "questions"
    done = "done"
    failed = "failed"


class TaskCreatedResponse(BaseModel):
    task_id: str
    status: TaskStatus = TaskStatus.pending


class GenerateTaskStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str
    status: TaskStatus
    step: TaskStep
    progress_message: str | None = None
    error_message: str | None = None
    result: GenerateQuestionsResponse | None = None


class ResearchTaskStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str
    status: TaskStatus
    step: TaskStep
    progress_message: str | None = None
    error_message: str | None = None
    result: ResearchResponse | None = None


class ResearchSessionSnapshot(BaseModel):
    research_session_id: str
    user_content: str
    materials: list[dict]
    candidates: list[dict]
    input_kind: str
    degraded_mode: str
    mock_mode: bool = False
