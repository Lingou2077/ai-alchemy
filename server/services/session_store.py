from schemas.knowledge import StructuredKnowledge
from schemas.question import QuestionSet


class SessionData:
    def __init__(
        self,
        session_id: str,
        source_content: str,
        knowledge: StructuredKnowledge,
        questions: QuestionSet,
    ):
        self.session_id = session_id
        self.source_content = source_content
        self.knowledge = knowledge
        self.questions = questions


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}

    def create(
        self,
        session_id: str,
        source_content: str,
        knowledge: StructuredKnowledge,
        questions: QuestionSet,
    ) -> SessionData:
        session = SessionData(session_id, source_content, knowledge, questions)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SessionData | None:
        return self._sessions.get(session_id)

    def clear(self) -> None:
        self._sessions.clear()


session_store = SessionStore()
