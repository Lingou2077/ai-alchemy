from __future__ import annotations

import time

from schemas.knowledge import StructuredKnowledge
from schemas.question import QuestionSet
from schemas.research import DegradedMode, InputKind, TopicCandidate, WebMaterial


class SessionData:
    def __init__(
        self,
        session_id: str,
        source_content: str,
        knowledge: StructuredKnowledge,
        questions: QuestionSet,
        *,
        research_session_id: str | None = None,
        selected_topic_id: str | None = None,
        grounding_mode: str | None = None,
        grounding_sources: list[str] | None = None,
        web_research_enabled: bool = False,
    ):
        self.session_id = session_id
        self.source_content = source_content
        self.knowledge = knowledge
        self.questions = questions
        self.research_session_id = research_session_id
        self.selected_topic_id = selected_topic_id
        self.grounding_mode = grounding_mode
        self.grounding_sources = grounding_sources or []
        self.web_research_enabled = web_research_enabled


class ResearchSessionData:
    def __init__(
        self,
        research_session_id: str,
        user_content: str,
        materials: list[WebMaterial],
        candidates: list[TopicCandidate],
        input_kind: InputKind,
        degraded_mode: DegradedMode,
        mock_mode: bool,
        created_at: float,
    ):
        self.research_session_id = research_session_id
        self.user_content = user_content
        self.materials = materials
        self.candidates = candidates
        self.input_kind = input_kind
        self.degraded_mode = degraded_mode
        self.mock_mode = mock_mode
        self.created_at = created_at


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}

    def create(
        self,
        session_id: str,
        source_content: str,
        knowledge: StructuredKnowledge,
        questions: QuestionSet,
        **kwargs: object,
    ) -> SessionData:
        session = SessionData(session_id, source_content, knowledge, questions, **kwargs)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SessionData | None:
        return self._sessions.get(session_id)

    def clear(self) -> None:
        self._sessions.clear()


class ResearchSessionStore:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._sessions: dict[str, ResearchSessionData] = {}
        self._ttl_seconds = ttl_seconds

    def create(
        self,
        *,
        research_session_id: str,
        user_content: str,
        materials: list[WebMaterial],
        candidates: list[TopicCandidate],
        input_kind: InputKind,
        degraded_mode: DegradedMode,
        mock_mode: bool,
    ) -> ResearchSessionData:
        session = ResearchSessionData(
            research_session_id=research_session_id,
            user_content=user_content,
            materials=materials,
            candidates=candidates,
            input_kind=input_kind,
            degraded_mode=degraded_mode,
            mock_mode=mock_mode,
            created_at=time.time(),
        )
        self._sessions[research_session_id] = session
        return session

    def get(self, research_session_id: str) -> ResearchSessionData | None:
        session = self._sessions.get(research_session_id)
        if session is None:
            return None
        if time.time() - session.created_at > self._ttl_seconds:
            del self._sessions[research_session_id]
            return None
        return session

    def clear(self) -> None:
        self._sessions.clear()


from config import settings

session_store = SessionStore()
research_store = ResearchSessionStore(ttl_seconds=settings.research_session_ttl_seconds)
