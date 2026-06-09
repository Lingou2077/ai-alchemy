import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from schemas.research import DegradedMode, InputKind
from services.research.mock_tavily_tools import build_mock_tavily_tools
from services.research.research_agent import run_research_agent, sanitize_tool_args


def _empty_search_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=lambda query, **kwargs: json.dumps({"results": []}),
        name="tavily_search",
        description="empty search mock",
    )


@pytest.mark.asyncio
async def test_research_agent_runs_search_tool_for_keyword():
    tools = build_mock_tavily_tools()
    tool_call = {
        "name": "tavily_search",
        "args": {"query": "Harness Engineering"},
        "id": "call-1",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="done"),
        ]
    )

    materials, mode, used = await run_research_agent(
        "Harness Engineering",
        InputKind.keyword,
        tools=tools,
        model=mock_model,
    )

    assert used == 1
    assert len(materials) >= 1
    assert mode.value in {"none", "partial"}


@pytest.mark.asyncio
async def test_research_agent_respects_max_tool_calls():
    tools = build_mock_tavily_tools()
    tool_call = {
        "name": "tavily_search",
        "args": {"query": "test"},
        "id": "call-1",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        return_value=AIMessage(content="", tool_calls=[tool_call])
    )

    materials, mode, used = await run_research_agent(
        "test",
        InputKind.keyword,
        tools=tools,
        model=mock_model,
    )

    assert used <= 4


@pytest.mark.asyncio
async def test_research_agent_runs_extract_for_url():
    tools = build_mock_tavily_tools()
    tool_call = {
        "name": "tavily_extract",
        "args": {"urls": ["https://en.wikipedia.org/wiki/Test"]},
        "id": "call-extract",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="done"),
        ]
    )

    materials, mode, used = await run_research_agent(
        "https://en.wikipedia.org/wiki/Test",
        InputKind.url,
        tools=tools,
        model=mock_model,
    )

    assert used == 1
    assert len(materials) >= 1
    assert materials[0].source == "extract"
    assert mode == DegradedMode.none


@pytest.mark.asyncio
async def test_research_agent_no_results_degraded_mode():
    tools = [_empty_search_tool()]
    tool_call = {
        "name": "tavily_search",
        "args": {"query": "nonexistent topic xyz"},
        "id": "call-empty",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="no results"),
        ]
    )

    materials, mode, used = await run_research_agent(
        "nonexistent topic xyz",
        InputKind.keyword,
        tools=tools,
        model=mock_model,
    )

    assert used == 1
    assert materials == []
    assert mode == DegradedMode.no_web_results


@pytest.mark.asyncio
async def test_research_agent_partial_on_tool_failure():
    tools = build_mock_tavily_tools()
    tool_calls = [
        {
            "name": "unknown_tool",
            "args": {},
            "id": "call-bad",
            "type": "tool_call",
        },
        {
            "name": "tavily_search",
            "args": {"query": "Harness Engineering"},
            "id": "call-ok",
            "type": "tool_call",
        },
    ]
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=tool_calls),
            AIMessage(content="done"),
        ]
    )

    materials, mode, used = await run_research_agent(
        "Harness Engineering",
        InputKind.keyword,
        tools=tools,
        model=mock_model,
    )

    assert used == 2
    assert len(materials) >= 1
    assert mode == DegradedMode.partial


def test_sanitize_tool_args_strips_forbidden_search_params():
    args = {
        "query": "harness engineering",
        "search_depth": "advanced",
        "max_results": 8,
        "include_answer": True,
    }
    sanitized = sanitize_tool_args("tavily_search", args)
    assert sanitized == {"query": "harness engineering", "search_depth": "advanced"}


def test_sanitize_tool_args_strips_forbidden_extract_params():
    args = {
        "urls": ["https://example.com"],
        "extract_depth": "advanced",
        "include_favicon": True,
    }
    sanitized = sanitize_tool_args("tavily_extract", args)
    assert sanitized == {"urls": ["https://example.com"], "extract_depth": "advanced"}


@pytest.mark.asyncio
async def test_research_agent_sanitizes_forbidden_search_params():
    tools = build_mock_tavily_tools()
    tool_call = {
        "name": "tavily_search",
        "args": {
            "query": "Harness Engineering",
            "search_depth": "advanced",
            "max_results": 8,
        },
        "id": "call-sanitize",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="done"),
        ]
    )
    invoked_args: dict = {}

    async def _track_invoke(tool, args):
        invoked_args.update(args)
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(args)
        return tool.invoke(args)

    with patch("services.research.research_agent._invoke_tool", new=_track_invoke):
        materials, mode, used = await run_research_agent(
            "Harness Engineering",
            InputKind.keyword,
            tools=tools,
            model=mock_model,
        )

    assert "max_results" not in invoked_args
    assert used == 1
    assert len(materials) >= 1
    assert mode == DegradedMode.none


@pytest.mark.asyncio
async def test_research_agent_tavily_api_error_no_materials():
    tools = build_mock_tavily_tools()
    tool_call = {
        "name": "tavily_search",
        "args": {"query": "test"},
        "id": "call-err",
        "type": "tool_call",
    }
    mock_model = MagicMock()
    mock_model.bind_tools.return_value = mock_model
    mock_model.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(content="", tool_calls=[tool_call]),
            AIMessage(content="done"),
        ]
    )

    async def _fail_tool(tool, args):
        return {"error": Exception("Error 401: Unauthorized")}

    with patch("services.research.research_agent._invoke_tool", new=_fail_tool):
        materials, mode, used = await run_research_agent(
            "test",
            InputKind.keyword,
            tools=tools,
            model=mock_model,
        )

    assert used == 1
    assert materials == []
    assert mode == DegradedMode.no_web_results
