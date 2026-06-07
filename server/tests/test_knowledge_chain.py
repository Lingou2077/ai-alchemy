import pytest
from langchain_core.runnables import RunnableLambda

from chains.knowledge_chain import build_knowledge_chain
from schemas.knowledge import StructuredKnowledge


@pytest.mark.asyncio
async def test_knowledge_chain_returns_structured_knowledge():
    async def fake_runner(_: dict):
        return StructuredKnowledge(
            topic="Go 并发编程基础",
            summary="goroutine 与 channel 是 Go 并发核心。",
            concepts=[],
            key_facts=[],
            misconceptions=[],
        )

    chain = build_knowledge_chain(structured_runner=RunnableLambda(fake_runner))
    result = await chain.ainvoke({"content": "Go 并发内容"})
    assert isinstance(result, StructuredKnowledge)
    assert result.topic == "Go 并发编程基础"
