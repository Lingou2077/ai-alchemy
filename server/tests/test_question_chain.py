import pytest
from langchain_core.runnables import RunnableLambda

from chains.question_chain import build_question_chain
from schemas.question import Level, Option, Question, QuestionSet


@pytest.mark.asyncio
async def test_question_chain_returns_question_set(sample_knowledge):
    async def fake_runner(_: dict):
        return QuestionSet(
            levels=[
                Level(
                    level_index=1,
                    questions=[
                        Question(
                            id="q1",
                            type="single",
                            difficulty="easy",
                            stem="题干",
                            options=[Option(key="A", text="选项A")],
                            answer=["A"],
                            explanation="解析",
                            concept_tags=["goroutine"],
                        )
                    ],
                )
            ]
        )

    chain = build_question_chain(structured_runner=RunnableLambda(fake_runner))
    result = await chain.ainvoke(
        {
            "structured_knowledge": sample_knowledge.model_dump_json(ensure_ascii=False),
            "count": 3,
        }
    )
    assert isinstance(result, QuestionSet)
    assert result.levels[0].questions[0].id == "q1"
