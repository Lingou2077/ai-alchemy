from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Option(BaseModel):
    key: str
    text: str


class Question(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["single", "multiple", "boolean"]
    difficulty: Literal["easy", "medium", "hard"]
    stem: str
    options: list[Option]
    answer: list[str]
    explanation: str
    concept_tags: list[str] = Field(default_factory=list, alias="conceptTags")


class QuestionPublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: Literal["single", "multiple", "boolean"]
    difficulty: Literal["easy", "medium", "hard"]
    stem: str
    options: list[Option]
    concept_tags: list[str] = Field(default_factory=list, alias="conceptTags")

    @classmethod
    def from_question(cls, question: Question) -> "QuestionPublic":
        return cls(
            id=question.id,
            type=question.type,
            difficulty=question.difficulty,
            stem=question.stem,
            options=question.options,
            conceptTags=question.concept_tags,
        )


class Level(BaseModel):
    level_index: int
    questions: list[Question]


class LevelPublic(BaseModel):
    level_index: int
    questions: list[QuestionPublic]


class QuestionSet(BaseModel):
    levels: list[Level]


class GenerateQuestionsRequest(BaseModel):
    content: str = Field(max_length=5000)
    questions_per_level: int = Field(default=5, ge=3, le=10)


class GenerateQuestionsResponse(BaseModel):
    session_id: str
    topic: str
    levels: list[LevelPublic]
    truncated: bool = False


class CheckAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    user_answer: list[str]


class CheckAnswerResponse(BaseModel):
    is_correct: bool
    explanation: str
    correct_answer: list[str]
