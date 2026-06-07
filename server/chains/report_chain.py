from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from chains.knowledge_chain import create_chat_model, load_prompt
from schemas.report import ReportData


def build_report_chain(
    model: BaseChatModel | None = None,
    structured_runner: Runnable | None = None,
):
    system_prompt = load_prompt("report.txt")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "知识结构：\n{structured_knowledge}\n\n"
                "答题记录：\n{answers_detail}\n\n"
                "本地统计：\n"
                "正确率：{accuracy}%\n"
                "用时：{duration}秒\n"
                "session_id：{session_id}\n"
                "topic：{topic}",
            ),
        ]
    )
    runner = structured_runner or (model or create_chat_model()).with_structured_output(
        ReportData,
        method="function_calling",
    )
    return prompt | runner
