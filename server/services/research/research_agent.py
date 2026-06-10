import asyncio
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from chains.knowledge_chain import create_chat_model, load_prompt
from config import settings
from schemas.research import DegradedMode, InputKind, WebMaterial
from services.research.context_budget import cap_materials_count, summarize_tool_result_for_agent
from services.research.materials import (
    dedupe_materials,
    is_tavily_error_result,
    materials_from_tool,
    resolve_degraded_mode,
)
from services.research.tavily_tool_factory import build_tavily_tools

logger = logging.getLogger(__name__)

_TAVILY_SEARCH_FORBIDDEN_INVOKE = frozenset(
    {
        "max_results",
        "include_answer",
        "include_raw_content",
        "include_image_descriptions",
        "include_favicon",
        "country",
        "exact_match",
        "auto_parameters",
        "include_usage",
    }
)
_TAVILY_EXTRACT_FORBIDDEN_INVOKE = frozenset(
    {
        "include_usage",
        "include_favicon",
        "format",
    }
)


def sanitize_tool_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "tavily_search":
        forbidden = _TAVILY_SEARCH_FORBIDDEN_INVOKE
    elif tool_name == "tavily_extract":
        forbidden = _TAVILY_EXTRACT_FORBIDDEN_INVOKE
    else:
        return dict(args)
    return {key: value for key, value in args.items() if key not in forbidden}


async def _invoke_tool(tool: BaseTool, args: dict[str, Any]) -> Any:
    if hasattr(tool, "ainvoke"):
        return await tool.ainvoke(args)
    return await asyncio.to_thread(tool.invoke, args)


async def run_research_agent(
    user_content: str,
    input_kind: InputKind,
    *,
    tools: list[BaseTool] | None = None,
    model: BaseChatModel | None = None,
) -> tuple[list[WebMaterial], DegradedMode, int]:
    tool_list = tools or build_tavily_tools()
    tool_map = {tool.name: tool for tool in tool_list}
    chat_model = (model or create_chat_model()).bind_tools(tool_list)

    system_prompt = load_prompt("research_agent.txt").format(
        input_kind=input_kind.value,
        max_tool_calls=settings.research_agent_max_tool_calls,
        user_content=user_content,
    )
    messages: list[Any] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请调研以下内容：\n{user_content}"),
    ]

    collected: list[WebMaterial] = []
    tool_calls_used = 0
    had_tool_failures = False
    timed_out = False

    async def _loop() -> None:
        nonlocal tool_calls_used, had_tool_failures
        for _ in range(settings.research_agent_max_tool_calls + 1):
            response = await chat_model.ainvoke(messages)
            if not isinstance(response, AIMessage) or not response.tool_calls:
                messages.append(response)
                return

            messages.append(response)
            for tool_call in response.tool_calls:
                if tool_calls_used >= settings.research_agent_max_tool_calls:
                    return
                tool_calls_used += 1
                tool = tool_map.get(tool_call["name"])
                if tool is None:
                    had_tool_failures = True
                    messages.append(
                        ToolMessage(
                            content='{"error":"unknown tool"}',
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                try:
                    tool_args = sanitize_tool_args(tool_call["name"], tool_call["args"])
                    result = await _invoke_tool(tool, tool_args)
                    if is_tavily_error_result(result):
                        had_tool_failures = True
                        messages.append(
                            ToolMessage(
                                content='{"error":"tavily api error"}',
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    collected.extend(materials_from_tool(tool_call["name"], result))
                    messages.append(
                        ToolMessage(
                            content=summarize_tool_result_for_agent(tool_call["name"], result),
                            tool_call_id=tool_call["id"],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    had_tool_failures = True
                    logger.warning("tool %s failed: %s", tool_call["name"], exc)
                    messages.append(
                        ToolMessage(
                            content='{"error":"tool failed"}',
                            tool_call_id=tool_call["id"],
                        )
                    )

    try:
        await asyncio.wait_for(_loop(), timeout=settings.research_agent_timeout_seconds)
    except TimeoutError:
        timed_out = True

    materials = cap_materials_count(dedupe_materials(collected))
    mode = resolve_degraded_mode(
        materials,
        had_tool_failures=had_tool_failures,
        timed_out=timed_out,
    )
    return materials, mode, tool_calls_used
