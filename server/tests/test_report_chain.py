import pytest
from langchain_core.runnables import RunnableLambda

from chains.report_chain import build_report_chain
from schemas.report import ConceptNode, ReportData, WeakPoint


@pytest.mark.asyncio
async def test_report_chain_returns_report_data(sample_knowledge):
    async def fake_runner(_: dict):
        return ReportData(
            sessionId="sid",
            topic="Go 并发编程基础",
            accuracy=80.0,
            totalQuestions=2,
            correctCount=1,
            wrongCount=1,
            duration=60,
            weakPoints=[WeakPoint(name="channel", reason="答错")],
            summary="总结",
            suggestion="建议",
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
    assert isinstance(result, ReportData)
    assert result.summary == "总结"
