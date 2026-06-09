from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


EXPLORE_ALL_TOPIC_ID = "__all__"


class InputKind(str, Enum):
    keyword = "keyword"
    url = "url"
    mixed = "mixed"
    text = "text"


class DegradedMode(str, Enum):
    none = "none"
    no_web_results = "no_web_results"
    partial = "partial"
    agent_timeout = "agent_timeout"


class WebMaterial(BaseModel):
    source: Literal["search", "extract", "text"]
    title: str = ""
    url: str = ""
    content: str
    score: float | None = None


class TopicCandidate(BaseModel):
    id: str
    title: str = Field(max_length=60)
    summary: str = Field(max_length=200)
    source_urls: list[str] = Field(default_factory=list)

    @field_validator("title", mode="before")
    @classmethod
    def truncate_title(cls, value: object) -> object:
        if isinstance(value, str) and len(value) > 60:
            return value[:60]
        return value

    @field_validator("summary", mode="before")
    @classmethod
    def truncate_summary(cls, value: object) -> object:
        if isinstance(value, str) and len(value) > 200:
            return value[:200]
        return value


class TopicCandidates(BaseModel):
    candidates: list[TopicCandidate]


class ResearchRequest(BaseModel):
    content: str = Field(max_length=5000)


class ResearchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    research_session_id: str
    candidates: list[TopicCandidate]
    input_kind: InputKind
    degraded_mode: DegradedMode = DegradedMode.none
    mock_mode: bool = False
    degraded_message: str | None = None
