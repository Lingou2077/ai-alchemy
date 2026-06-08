from pydantic import BaseModel, ConfigDict, Field


class QuizHistoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    topic: str
    accuracy: float
    question_count: int = Field(alias="questionCount")
    duration_sec: int = Field(alias="durationSec")
    status: str
    finished_at: str = Field(alias="finishedAt")


class QuizHistoryDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    topic: str
    accuracy: float
    question_count: int = Field(alias="questionCount")
    duration_sec: int = Field(alias="durationSec")
    status: str
    summary: str | None = None
    suggestion: str | None = None
    weak_points: list[dict] = Field(default_factory=list, alias="weakPoints")
    finished_at: str = Field(alias="finishedAt")


class QuizHistoryListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[QuizHistoryItem]
    total: int
    page: int
    limit: int


class WrongQuestionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    question_id: str = Field(alias="questionId")
    topic: str
    stem: str
    difficulty: str
    wrong_count: int = Field(alias="wrongCount")
    last_wrong_at: str = Field(alias="lastWrongAt")


class WrongQuestionDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    question_id: str = Field(alias="questionId")
    topic: str
    stem: str
    options: list[dict]
    correct_answer: list[str] = Field(alias="correctAnswer")
    explanation: str
    difficulty: str
    wrong_count: int = Field(alias="wrongCount")
    last_wrong_at: str = Field(alias="lastWrongAt")


class WrongQuestionListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[WrongQuestionItem]
    total: int
    page: int
    limit: int


class ExpGain(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: int
    leveled_up: bool = Field(alias="leveledUp")
    new_level: int = Field(alias="newLevel")
    new_title: str = Field(alias="newTitle")
    level_before: int = Field(alias="levelBefore")


class ReportStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    compare_last_accuracy: float | None = Field(default=None, alias="compareLastAccuracy")
    weekly_quiz_index: int | None = Field(default=None, alias="weeklyQuizIndex")
    related_history: list[QuizHistoryItem] = Field(default_factory=list, alias="relatedHistory")
