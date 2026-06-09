from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from chains.knowledge_chain import create_chat_model, load_prompt
from schemas.question import QuestionSet


def build_question_chain(
    model: BaseChatModel | None = None,
    structured_runner: Runnable | None = None,
    prompt_file: str = "question.txt",
):
    system_prompt = load_prompt(prompt_file)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "结构化知识：\n{structured_knowledge}\n\n请生成 {count} 道题。",
            ),
        ]
    )
    runner = structured_runner or (model or create_chat_model()).with_structured_output(
        QuestionSet,
        method="function_calling",
    )
    return prompt | runner
