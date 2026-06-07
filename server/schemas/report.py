from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WeakPoint(BaseModel):
    name: str
    reason: str


class ConceptNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    mastery: Literal["mastered", "partial", "weak"]
    related_question_count: int = Field(alias="relatedQuestionCount")


class AnswerRecord(BaseModel):
    question_id: str
    user_answer: list[str]
    is_correct: bool
    time_spent: int


class GenerateReportRequest(BaseModel):
    session_id: str
    answers: list[AnswerRecord]


class ReportData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    topic: str
    accuracy: float
    total_questions: int = Field(alias="totalQuestions")
    correct_count: int = Field(alias="correctCount")
    wrong_count: int = Field(alias="wrongCount")
    duration: int
    weak_points: list[WeakPoint] = Field(default_factory=list, alias="weakPoints")
    summary: str
    suggestion: str
    concept_mastery: list[ConceptNode] = Field(default_factory=list, alias="conceptMastery")
