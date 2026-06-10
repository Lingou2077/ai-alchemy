from unittest.mock import patch

import pytest
from langchain_core.runnables import RunnableLambda

from chains.report_chain import build_report_chain
from schemas.report import (
    AnswerRecord,
    ConceptNode,
    GenerateReportRequest,
    ReportLLMOutput,
    WeakPoint,
)
from services.question_pipeline import run_report_pipeline
from services.report_sanitize import contains_emoji, sanitize_report_llm_output, strip_emoji_and_symbols
from services.session_store import session_store


def assert_plain_text(text: str) -> None:
    assert not contains_emoji(text)


@pytest.mark.asyncio
async def test_report_chain_returns_report_llm_output(sample_knowledge):
    async def fake_runner(_: dict):
        return ReportLLMOutput(
            sessionId="sid",
            topic="Go 并发编程基础",
            summary="总结",
            suggestion="建议",
            shareTagline="channel 待精炼",
            weakPoints=[WeakPoint(name="channel", reason="答错")],
            conceptMastery=[
                ConceptNode(name="goroutine", mastery="mastered", relatedQuestionCount=1)
            ],
        )

    chain = build_report_chain(structured_runner=RunnableLambda(fake_runner))
    result = await chain.ainvoke(
        {
            "structured_knowledge": sample_knowledge.model_dump_json(ensure_ascii=False),
            "answers_detail": "题目 q1 错误",
            "accuracy": 50,
            "duration": 60,
            "session_id": "sid",
            "topic": sample_knowledge.topic,
        }
    )
    assert isinstance(result, ReportLLMOutput)
    assert result.summary == "总结"
    assert result.share_tagline == "channel 待精炼"


@pytest.mark.asyncio
async def test_run_report_pipeline_applies_share_tagline_fallback(
    sample_knowledge,
    sample_question_set,
):
    session_store.create("sid-tagline", "text", sample_knowledge, sample_question_set)

    async def fake_runner(_: dict):
        return ReportLLMOutput(
            summary="总结",
            suggestion="建议",
            shareTagline="",
        )

    fake_chain = RunnableLambda(fake_runner)
    with patch("services.question_pipeline.build_report_chain", return_value=fake_chain):
        report = await run_report_pipeline(
            GenerateReportRequest(
                session_id="sid-tagline",
                answers=[
                    AnswerRecord(
                        question_id="q1",
                        user_answer=["A"],
                        is_correct=True,
                        time_spent=1000,
                    )
                ],
                quiz_status="completed",
            )
        )

    assert report.share_tagline
    assert len(report.share_tagline) <= 20
    assert_plain_text(report.share_tagline)


@pytest.mark.asyncio
async def test_run_report_pipeline_sanitizes_emoji_share_tagline(
    sample_knowledge,
    sample_question_set,
):
    session_store.create("sid-emoji", "text", sample_knowledge, sample_question_set)
    long_tagline = "🎯 五题全中！goroutine channel 炼金术已大成"

    async def fake_runner(_: dict):
        return ReportLLMOutput(
            summary="✨ 纯总结",
            suggestion="建议",
            shareTagline=long_tagline,
        )

    fake_chain = RunnableLambda(fake_runner)
    with patch("services.question_pipeline.build_report_chain", return_value=fake_chain):
        report = await run_report_pipeline(
            GenerateReportRequest(
                session_id="sid-emoji",
                answers=[
                    AnswerRecord(
                        question_id="q1",
                        user_answer=["A"],
                        is_correct=True,
                        time_spent=1000,
                    )
                ],
                quiz_status="completed",
            )
        )

    assert len(report.share_tagline) <= 20
    assert_plain_text(report.share_tagline)
    assert_plain_text(report.summary)
    assert "🎯" not in report.share_tagline
    assert "✨" not in report.summary


def test_sanitize_report_llm_output_strips_emoji_from_all_text_fields():
    raw = ReportLLMOutput(
        summary="✨ 核心总结",
        suggestion="🔥 继续加油",
        shareTagline="🎯 炼金成功",
        weakPoints=[WeakPoint(name="channel", reason="❌ 答错")],
        conceptMastery=[ConceptNode(name="goroutine", mastery="weak", relatedQuestionCount=1)],
    )
    cleaned = sanitize_report_llm_output(raw)
    assert cleaned.summary == "核心总结"
    assert cleaned.suggestion == "继续加油"
    assert cleaned.share_tagline == "炼金成功"
    assert cleaned.weak_points[0].reason == "答错"
    assert_plain_text(cleaned.summary)


def test_strip_emoji_and_symbols():
    assert strip_emoji_and_symbols("  🎯 五题全中！  ") == "五题全中！"
