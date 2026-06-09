import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse, urlunparse

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

SERVER_DIR = Path(__file__).resolve().parent.parent
load_dotenv(SERVER_DIR / ".env")


def _to_test_database_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.endswith("/ai_alchemy_test") or path.endswith("ai_alchemy_test"):
        return url
    if path.endswith("/ai_alchemy") or path.endswith("ai_alchemy"):
        new_path = f"{path}_test"
        return urlunparse(parsed._replace(path=new_path))
    return url


database_url = os.getenv("DATABASE_URL", "")
if database_url:
    os.environ["DATABASE_URL"] = _to_test_database_url(database_url)

os.environ["DEV_MOCK_LOGIN"] = "true"
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from db.models.exp_log import ExpLog  # noqa: E402
from db.models.generation_task import GenerationTask  # noqa: E402
from db.models.quiz_record import QuizRecord  # noqa: E402
from db.models.user import User  # noqa: E402
from db.models.wrong_question import WrongQuestion  # noqa: E402
from db.session import get_db, get_engine  # noqa: E402
from main import app  # noqa: E402
from schemas.knowledge import Concept, StructuredKnowledge  # noqa: E402
from schemas.question import Level, Option, Question, QuestionSet  # noqa: E402
from services.session_store import research_store, session_store  # noqa: E402


@pytest.fixture(autouse=True)
def clear_sessions():
    session_store.clear()
    research_store.clear()
    yield
    session_store.clear()
    research_store.clear()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
async def client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    class _SharedSessionFactory:
        def __call__(self) -> Session:
            return db_session

    def override_session_factory() -> _SharedSessionFactory:
        return _SharedSessionFactory()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    with patch("services.generation_task_service.get_session_factory", override_session_factory):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    db_session.query(ExpLog).delete()
    db_session.query(WrongQuestion).delete()
    db_session.query(QuizRecord).delete()
    db_session.query(GenerationTask).delete()
    db_session.query(User).delete()
    db_session.commit()
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_factory(db_session: Session):
    def _factory(exp: int = 0, openid: str = "factory-user") -> User:
        user = User(openid=openid, exp=exp, level=1, title="见习炼金师")
        db_session.add(user)
        db_session.flush()
        return user

    return _factory


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
