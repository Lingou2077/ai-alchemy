import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from schemas.knowledge import Concept, StructuredKnowledge
from schemas.question import Level, Option, Question, QuestionSet
from services.session_store import session_store


@pytest.fixture(autouse=True)
def clear_sessions():
    session_store.clear()
    yield
    session_store.clear()


@pytest.fixture
def sample_knowledge() -> StructuredKnowledge:
    return StructuredKnowledge(
        topic="Go 并发编程基础",
        summary="goroutine 与 channel 是 Go 并发核心。",
        concepts=[
            Concept(
                name="goroutine",
                description="轻量级线程",
                importance="high",
            ),
            Concept(
                name="channel",
                description="goroutine 间通信",
                importance="high",
            ),
        ],
        key_facts=["goroutine 初始栈约 2KB", "channel 遵循 CSP 模型"],
        misconceptions=["goroutine 栈与 OS 线程一样大"],
    )


@pytest.fixture
def sample_question_set() -> QuestionSet:
    questions = [
        Question(
            id="q1",
            type="single",
            difficulty="medium",
            stem="Go 语言中，goroutine 的默认栈大小是多少？",
            options=[
                Option(key="A", text="2 KB"),
                Option(key="B", text="8 KB"),
                Option(key="C", text="1 MB"),
                Option(key="D", text="2 MB"),
            ],
            answer=["A"],
            explanation="goroutine 初始栈仅 2KB。",
            concept_tags=["goroutine"],
        ),
        Question(
            id="q2",
            type="boolean",
            difficulty="easy",
            stem="channel 可用于 goroutine 之间通信。",
            options=[
                Option(key="T", text="正确"),
                Option(key="F", text="错误"),
            ],
            answer=["T"],
            explanation="channel 是 Go 推荐的通信方式。",
            concept_tags=["channel"],
        ),
    ]
    return QuestionSet(levels=[Level(level_index=1, questions=questions)])


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
