import json
from typing import Any

from schemas.research import DegradedMode, WebMaterial
from services.research.context_budget import truncate_content_for_storage


def is_tavily_error_result(raw: Any) -> bool:
    if isinstance(raw, dict) and raw.get("error") is not None:
        return True
    data = _parse_payload(raw)
    return isinstance(data, dict) and data.get("error") is not None


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


def materials_from_search_result(raw: Any) -> list[WebMaterial]:
    data = _parse_payload(raw)
    materials: list[WebMaterial] = []
    for item in data.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        content = (item.get("content") or item.get("raw_content") or "").strip()
        if not content:
            continue
        materials.append(
            WebMaterial(
                source="search",
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                content=truncate_content_for_storage(content, "search"),
                score=float(item["score"]) if item.get("score") is not None else None,
            )
        )
    return materials


def materials_from_extract_result(raw: Any) -> list[WebMaterial]:
    data = _parse_payload(raw)
    materials: list[WebMaterial] = []
    for item in data.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        content = (item.get("raw_content") or item.get("content") or "").strip()
        if not content:
            continue
        url = str(item.get("url") or "")
        materials.append(
            WebMaterial(
                source="extract",
                title=url,
                url=url,
                content=truncate_content_for_storage(content, "extract"),
                score=None,
            )
        )
    return materials


def materials_from_tool(tool_name: str, raw: Any) -> list[WebMaterial]:
    if tool_name == "tavily_search":
        return materials_from_search_result(raw)
    if tool_name == "tavily_extract":
        return materials_from_extract_result(raw)
    return []


def dedupe_materials(materials: list[WebMaterial]) -> list[WebMaterial]:
    seen: set[str] = set()
    unique: list[WebMaterial] = []
    for item in materials:
        key = item.url or item.content[:120]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def is_material_usable(material: WebMaterial) -> bool:
    return len(material.content.strip()) >= 20


def filter_usable_materials(materials: list[WebMaterial]) -> list[WebMaterial]:
    return [item for item in materials if is_material_usable(item)]


def fallback_text_material(content: str) -> WebMaterial:
    return WebMaterial(
        source="text",
        title="用户输入",
        url="",
        content=content.strip(),
        score=None,
    )


def resolve_degraded_mode(
    materials: list[WebMaterial],
    *,
    had_tool_failures: bool,
    timed_out: bool,
) -> DegradedMode:
    if not materials:
        return DegradedMode.agent_timeout if timed_out else DegradedMode.no_web_results
    if had_tool_failures:
        return DegradedMode.partial
    return DegradedMode.none


def degraded_user_message(mode: DegradedMode) -> str | None:
    if mode == DegradedMode.none:
        return None
    if mode == DegradedMode.partial:
        return "部分网页资料获取失败，将结合已检索到的内容继续"
    if mode == DegradedMode.agent_timeout:
        return "联网检索超时，将主要依据您输入的内容"
    return "未找到足够网页资料，将主要依据您输入的内容"


def apply_materials_fallback(
    materials: list[WebMaterial],
    user_content: str,
    mode: DegradedMode,
) -> tuple[list[WebMaterial], DegradedMode]:
    usable = filter_usable_materials(materials)
    if usable:
        return usable, mode if mode != DegradedMode.no_web_results else DegradedMode.none
    text = user_content.strip()
    if not text:
        return [], mode
    return [fallback_text_material(text)], (
        DegradedMode.agent_timeout if mode == DegradedMode.agent_timeout else DegradedMode.no_web_results
    )
