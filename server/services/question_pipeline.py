import logging
import uuid
from typing import Any

from fastapi import HTTPException

from chains.knowledge_chain import build_knowledge_chain
from chains.question_chain import build_question_chain
from chains.report_chain import build_report_chain
from config import settings
from schemas.knowledge import StructuredKnowledge
from schemas.question import (
    GenerateQuestionsResponse,
    LevelPublic,
    Question,
    QuestionPublic,
    QuestionSet,
)
from schemas.report import AnswerRecord, GenerateReportRequest, ReportData
from services.session_store import session_store

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 2


def _step_failure_detail(step_name: str) -> str:
    if step_name == "知识解析":
        return "知识解析失败，请精简内容后重试"
    return f"{step_name}失败，请重试"


def normalize_content(content: str) -> tuple[str, bool]:
    text = content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="请输入学习内容")
    truncated = False
    if len(text) > settings.content_max_length:
        raise HTTPException(status_code=400, detail="内容超过 5000 字上限")
    if len(text) > settings.content_truncate_length:
        text = text[: settings.content_truncate_length]
        truncated = True
    return text, truncated


def find_question(session_id: str, question_id: str) -> Question:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    for level in session.questions.levels:
        for question in level.questions:
            if question.id == question_id:
                return question
    raise HTTPException(status_code=404, detail="题目不存在")


def check_answer(question: Question, user_answer: list[str]) -> bool:
    normalized_user = sorted({answer.strip().upper() for answer in user_answer if answer.strip()})
    normalized_correct = sorted({answer.strip().upper() for answer in question.answer})
    return normalized_user == normalized_correct


async def invoke_with_retry(chain, payload: dict[str, Any], step_name: str):
    last_error: Exception | None = None
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            result = await chain.ainvoke(payload)
            if result is not None:
                return result
            logger.warning("%s returned None (attempt %d/%d)", step_name, attempt, _RETRY_ATTEMPTS)
        except Exception as exc:  # noqa: BLE001 - retry boundary
            last_error = exc
            logger.warning(
                "%s raised %s (attempt %d/%d): %s",
                step_name,
                type(exc).__name__,
                attempt,
                _RETRY_ATTEMPTS,
                exc,
            )
    raise HTTPException(status_code=503, detail=_step_failure_detail(step_name)) from last_error


async def run_question_pipeline(content: str, count: int) -> tuple[str, StructuredKnowledge, QuestionSet, bool]:
    normalized_content, truncated = normalize_content(content)
    knowledge_chain = build_knowledge_chain()
    question_chain = build_question_chain()

    knowledge = await invoke_with_retry(
        knowledge_chain,
        {"content": normalized_content},
        "知识解析",
    )
    questions = await invoke_with_retry(
        question_chain,
        {
            "structured_knowledge": knowledge.model_dump_json(ensure_ascii=False),
            "count": count,
        },
        "出题",
    )

    session_id = str(uuid.uuid4())
    session_store.create(session_id, normalized_content, knowledge, questions)
    return session_id, knowledge, questions, truncated


def build_generate_response(
    session_id: str,
    knowledge: StructuredKnowledge,
    questions: QuestionSet,
    truncated: bool,
) -> GenerateQuestionsResponse:
    public_levels = [
        LevelPublic(
            level_index=level.level_index,
            questions=[QuestionPublic.from_question(q) for q in level.questions],
        )
        for level in questions.levels
    ]
    return GenerateQuestionsResponse(
        session_id=session_id,
        topic=knowledge.topic,
        levels=public_levels,
        truncated=truncated,
    )


def build_answers_detail(answers: list[AnswerRecord]) -> str:
    lines = []
    for item in answers:
        status = "正确" if item.is_correct else "错误"
        lines.append(
            f"- 题目 {item.question_id}: 用户答案 {item.user_answer}，结果 {status}，用时 {item.time_spent}ms"
        )
    return "\n".join(lines) if lines else "无答题记录"


def compute_report_stats(answers: list[AnswerRecord]) -> tuple[float, int, int, int, int]:
    total = len(answers)
    correct = sum(1 for item in answers if item.is_correct)
    wrong = total - correct
    duration_ms = sum(item.time_spent for item in answers)
    duration_seconds = max(1, duration_ms // 1000)
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    return accuracy, total, correct, wrong, duration_seconds


async def run_report_pipeline(request: GenerateReportRequest) -> ReportData:
    session = session_store.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    accuracy, total, correct, wrong, duration = compute_report_stats(request.answers)
    if request.duration_sec is not None and request.duration_sec > 0:
        duration = request.duration_sec
    report_chain = build_report_chain()
    report = await invoke_with_retry(
        report_chain,
        {
            "structured_knowledge": session.knowledge.model_dump_json(ensure_ascii=False),
            "answers_detail": build_answers_detail(request.answers),
            "accuracy": accuracy,
            "duration": duration,
            "session_id": request.session_id,
            "topic": session.knowledge.topic,
        },
        "报告生成",
    )

    report.session_id = request.session_id
    report.topic = session.knowledge.topic
    report.accuracy = accuracy
    report.total_questions = total
    report.correct_count = correct
    report.wrong_count = wrong
    report.duration = duration
    return report
