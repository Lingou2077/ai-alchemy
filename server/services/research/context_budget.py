import json
from typing import Any

from config import settings
from schemas.research import WebMaterial


def truncate_head(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 1:
        return "…"
    return text[:limit - 1] + "…"


def truncate_head_tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 2:
        return truncate_head(text, limit)
    available = limit - 1
    head_len = int(available * 0.7)
    tail_len = available - head_len
    if tail_len < 10:
        return truncate_head(text, limit)
    return text[:head_len] + "…" + text[-tail_len:]


def truncate_content_for_storage(content: str, source: str) -> str:
    if source == "search":
        return truncate_head(content, settings.search_content_max)
    if source == "extract":
        return truncate_head_tail(content, settings.extract_content_max)
    return content


def sort_materials_by_score(materials: list[WebMaterial]) -> list[WebMaterial]:
    return sorted(
        materials,
        key=lambda item: item.score if item.score is not None else 0.0,
        reverse=True,
    )


def cap_materials_count(materials: list[WebMaterial]) -> list[WebMaterial]:
    return sort_materials_by_score(materials)[: settings.materials_max_count]


def _format_material_block(
    item: WebMaterial,
    *,
    include_source_in_title: bool = False,
    url_line_prefix: str = "来源",
) -> str:
    title = item.title or item.url or "material"
    if include_source_in_title:
        block = f"### {title} ({item.source})"
    else:
        block = f"### {title}"
    if item.url:
        block += f"\n{url_line_prefix}: {item.url}"
    block += f"\n{item.content}"
    return block


def format_materials_for_prompt(
    materials: list[WebMaterial],
    budget: int,
    *,
    include_source_in_title: bool = False,
    url_line_prefix: str = "来源",
    empty_text: str = "",
) -> str:
    if not materials:
        return empty_text
    lines: list[str] = []
    used = 0
    for item in sort_materials_by_score(materials):
        block = _format_material_block(
            item,
            include_source_in_title=include_source_in_title,
            url_line_prefix=url_line_prefix,
        )
        if used + len(block) > budget:
            remaining = budget - used
            if remaining > 100:
                lines.append(truncate_head(block, remaining))
            break
        lines.append(block)
        used += len(block) + 2
    return "\n\n".join(lines)


def _parse_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        if raw.get("error") is not None:
            return {}
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def summarize_tool_result_for_agent(tool_name: str, raw: Any) -> str:
    data = _parse_payload(raw)
    preview_limit = settings.agent_tool_content_preview_chars

    if tool_name == "tavily_search":
        results = data.get("results", []) or []
        lines = [f"tavily_search: {len(results)} results"]
        for item in results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            url = str(item.get("url") or "")
            content = (item.get("content") or item.get("raw_content") or "").strip()
            preview = truncate_head(content, preview_limit)
            score = item.get("score")
            score_str = f"[{float(score):.2f}] " if score is not None else ""
            lines.append(f"- {score_str}{title} | {url} | {preview}")
        return truncate_head("\n".join(lines), settings.agent_tool_message_max_chars)

    if tool_name == "tavily_extract":
        results = data.get("results", []) or []
        lines = [f"tavily_extract: {len(results)} pages"]
        for item in results:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "")
            raw_content = (item.get("raw_content") or item.get("content") or "").strip()
            stored_len = min(len(raw_content), settings.extract_content_max)
            lines.append(f"- {url} | 原文约{len(raw_content)}字, 已入库约{stored_len}字")
            if raw_content:
                preview = truncate_head(raw_content, preview_limit)
                lines.append(f"  预览: {preview}")
        failed = data.get("failed_results", []) or []
        if failed:
            lines.append(f"  失败: {len(failed)} URLs")
        return truncate_head("\n".join(lines), settings.agent_tool_message_max_chars)

    return truncate_head(str(raw), settings.agent_tool_message_max_chars)
