from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    code: str


class ExpProgress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current: int
    required: int
    total_exp: int = Field(alias="totalExp")


class UserStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_quizzes: int = Field(alias="totalQuizzes")
    average_accuracy: float = Field(alias="averageAccuracy")
    wrong_question_count: int = Field(alias="wrongQuestionCount")
    weekly_quiz_count: int = Field(alias="weeklyQuizCount")


class UserPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    nickname: str
    avatar_url: str = Field(alias="avatarUrl")
    exp: int
    level: int
    title: str
    total_quizzes: int = Field(alias="totalQuizzes")
    created_at: str | None = Field(default=None, alias="createdAt")
    exp_progress: ExpProgress = Field(alias="expProgress")
    stats: UserStats


class LoginResponse(BaseModel):
    token: str
    user: UserPublic


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nickname: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
