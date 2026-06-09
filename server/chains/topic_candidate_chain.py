from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from chains.knowledge_chain import create_chat_model, load_prompt
from schemas.research import TopicCandidates


def build_topic_candidate_chain(
    model: BaseChatModel | None = None,
    structured_runner: Runnable | None = None,
):
    system_prompt = load_prompt("topic_candidate.txt")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "用户原始输入：\n{user_content}\n\n联网材料：\n{materials_text}\n\n请输出候选主题。",
            ),
        ]
    )
    runner = structured_runner or (model or create_chat_model()).with_structured_output(
        TopicCandidates,
        method="function_calling",
    )
    return prompt | runner
