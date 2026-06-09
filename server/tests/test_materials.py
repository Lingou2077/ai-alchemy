import json

from schemas.research import DegradedMode, WebMaterial
from services.research.materials import (
    apply_materials_fallback,
    dedupe_materials,
    degraded_user_message,
    is_tavily_error_result,
    materials_from_tool,
    resolve_degraded_mode,
)


def test_materials_from_search():
    payload = {
        "results": [
            {
                "title": "A",
                "url": "https://a.com",
                "content": "content a",
                "score": 0.9,
            }
        ]
    }
    items = materials_from_tool("tavily_search", json.dumps(payload))
    assert len(items) == 1
    assert items[0].source == "search"


def test_materials_from_extract():
    payload = {
        "results": [
            {
                "url": "https://b.com",
                "raw_content": "full page content here for testing",
            }
        ]
    }
    items = materials_from_tool("tavily_extract", payload)
    assert len(items) == 1
    assert items[0].source == "extract"


def test_resolve_degraded_no_results():
    assert (
        resolve_degraded_mode([], had_tool_failures=False, timed_out=False)
        == DegradedMode.no_web_results
    )


def test_apply_materials_fallback():
    materials, mode = apply_materials_fallback([], "用户输入", DegradedMode.no_web_results)
    assert len(materials) == 1
    assert materials[0].source == "text"
    assert mode == DegradedMode.no_web_results


def test_resolve_degraded_partial():
    materials = [
        WebMaterial(
            source="search",
            title="A",
            url="https://a.com",
            content="enough content for usability check",
            score=0.9,
        )
    ]
    assert (
        resolve_degraded_mode(materials, had_tool_failures=True, timed_out=False)
        == DegradedMode.partial
    )


def test_resolve_degraded_timeout():
    assert (
        resolve_degraded_mode([], had_tool_failures=False, timed_out=True)
        == DegradedMode.agent_timeout
    )


def test_dedupe_materials_by_url():
    a = WebMaterial(source="search", title="A", url="https://dup.com", content="first", score=0.9)
    b = WebMaterial(source="search", title="B", url="https://dup.com", content="second", score=0.8)
    assert len(dedupe_materials([a, b])) == 1


def test_materials_from_tool_api_error():
    assert materials_from_tool("tavily_search", {"error": "unauthorized"}) == []
    assert is_tavily_error_result({"error": Exception("401")}) is True


def test_degraded_user_message():
    assert degraded_user_message(DegradedMode.none) is None
    assert "超时" in degraded_user_message(DegradedMode.agent_timeout)
    assert "未找到" in degraded_user_message(DegradedMode.no_web_results)
