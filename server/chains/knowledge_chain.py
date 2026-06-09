from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from config import settings
from schemas.knowledge import StructuredKnowledge

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def create_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key or "test-key",
        base_url=settings.deepseek_base_url,
        timeout=settings.ai_timeout_seconds,
        temperature=0.3,
    )


def build_knowledge_chain(
    model: BaseChatModel | None = None,
    structured_runner: Runnable | None = None,
    prompt_file: str = "knowledge.txt",
    human_template: str = "学习材料：\n{content}",
):
    system_prompt = load_prompt(prompt_file)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_template),
        ]
    )
    runner = structured_runner or (model or create_chat_model()).with_structured_output(
        StructuredKnowledge,
        method="function_calling",
    )
    return prompt | runner
