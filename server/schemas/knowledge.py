from typing import Literal

from pydantic import BaseModel, Field


class Concept(BaseModel):
    name: str
    description: str
    importance: Literal["high", "medium", "low"]


class StructuredKnowledge(BaseModel):
    topic: str
    summary: str
    concepts: list[Concept]
    key_facts: list[str]
    misconceptions: list[str]
