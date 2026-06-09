"""Live Tavily API tests — only run when explicitly enabled.

Usage (PowerShell):
    $env:RUN_TAVILY_LIVE_TESTS=1
    pytest tests/test_tavily_live.py -m integration -q

Requires a valid TAVILY_API_KEY in server/.env and TAVILY_MOCK=false.
"""

import os

import pytest

from services.research.materials import is_tavily_error_result, materials_from_tool
from services.research.tavily_tool_factory import build_tavily_tools, use_mock_tavily

RUN_LIVE = os.getenv("RUN_TAVILY_LIVE_TESTS", "").lower() in ("1", "true", "yes")
_KEY = os.getenv("TAVILY_API_KEY", "").strip()
SKIP_LIVE = not RUN_LIVE or use_mock_tavily() or not _KEY
SKIP_REASON = (
    "Set RUN_TAVILY_LIVE_TESTS=1 with valid TAVILY_API_KEY and TAVILY_MOCK=false"
)


def _assert_tavily_ok(result: object) -> None:
    if is_tavily_error_result(result):
        pytest.fail(
            "Tavily API 调用失败（请检查 TAVILY_API_KEY 是否完整、有效，"
            "在 Tavily 控制台重新复制密钥后重启服务）"
        )


@pytest.mark.integration
@pytest.mark.skipif(SKIP_LIVE, reason=SKIP_REASON)
@pytest.mark.skipif(len(_KEY) < 20, reason="TAVILY_API_KEY 过短，可能未粘贴完整密钥")
@pytest.mark.asyncio
async def test_live_tavily_search_returns_materials():
    tools = build_tavily_tools()
    search_tool = next(t for t in tools if t.name == "tavily_search")
    result = await search_tool.ainvoke({"query": "Harness Engineering AI"})
    _assert_tavily_ok(result)
    materials = materials_from_tool("tavily_search", result)
    assert len(materials) >= 1
    assert any(len(m.content.strip()) >= 20 for m in materials)


@pytest.mark.integration
@pytest.mark.skipif(SKIP_LIVE, reason=SKIP_REASON)
@pytest.mark.skipif(len(_KEY) < 20, reason="TAVILY_API_KEY 过短，可能未粘贴完整密钥")
@pytest.mark.asyncio
async def test_live_tavily_extract_returns_materials():
    tools = build_tavily_tools()
    extract_tool = next(t for t in tools if t.name == "tavily_extract")
    result = await extract_tool.ainvoke(
        {"urls": ["https://en.wikipedia.org/wiki/Go_(programming_language)"]}
    )
    _assert_tavily_ok(result)
    materials = materials_from_tool("tavily_extract", result)
    assert len(materials) >= 1
    assert any(len(m.content.strip()) >= 20 for m in materials)
