from schemas.knowledge import StructuredKnowledge
from schemas.question import Level, QuestionSet
from services.session_store import SessionStore


def test_create_and_get_session(sample_knowledge: StructuredKnowledge, sample_question_set: QuestionSet):
    store = SessionStore()
    session = store.create("sid-1", "source text", sample_knowledge, sample_question_set)

    assert session.session_id == "sid-1"
    assert store.get("sid-1") is session
    assert store.get("missing") is None


def test_clear_sessions(sample_knowledge: StructuredKnowledge, sample_question_set: QuestionSet):
    store = SessionStore()
    store.create("sid-1", "source text", sample_knowledge, sample_question_set)
    store.clear()
    assert store.get("sid-1") is None
