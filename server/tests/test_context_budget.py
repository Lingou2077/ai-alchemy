import json

from schemas.research import WebMaterial
from services.research.context_budget import (
    cap_materials_count,
    format_materials_for_prompt,
    summarize_tool_result_for_agent,
    truncate_content_for_storage,
    truncate_head,
    truncate_head_tail,
)


def test_truncate_head():
    assert truncate_head("abcdef", 10) == "abcdef"
    assert truncate_head("abcdef", 3) == "ab…"


def test_truncate_head_tail_preserves_ends():
    text = "A" * 100 + "MIDDLE" + "B" * 100
    result = truncate_head_tail(text, 50)
    assert result.startswith("A")
    assert result.endswith("B")
    assert "…" in result
    assert len(result) <= 50


def test_truncate_content_for_storage_search():
    long = "x" * 3000
    result = truncate_content_for_storage(long, "search")
    assert len(result) <= 2001


def test_truncate_content_for_storage_extract():
    text = "H" * 2000 + "M" * 2000 + "T" * 2000
    result = truncate_content_for_storage(text, "extract")
    assert len(result) <= 4500
    assert result.startswith("H")
    assert result.endswith("T")


def test_format_materials_for_prompt_respects_budget():
    materials = [
        WebMaterial(
            source="search",
            title=f"Item {index}",
            url=f"https://example.com/{index}",
            content="content block " * 200,
            score=float(index),
        )
        for index in range(5)
    ]
    text = format_materials_for_prompt(materials, 500)
    assert len(text) <= 500


def test_cap_materials_count():
    materials = [
        WebMaterial(
            source="search",
            title=f"T{index}",
            url=f"https://a.com/{index}",
            content="enough content for usability",
            score=float(index),
        )
        for index in range(25)
    ]
    capped = cap_materials_count(materials)
    assert len(capped) == 20
    assert capped[0].score == 24.0


def test_summarize_tool_result_for_search():
    payload = {
        "results": [
            {
                "title": "Article",
                "url": "https://example.com",
                "content": "snippet text here",
                "score": 0.91,
            }
        ]
    }
    summary = summarize_tool_result_for_agent("tavily_search", json.dumps(payload))
    assert "tavily_search" in summary
    assert "Article" in summary
    assert "snippet text here" in summary
    assert "0.91" in summary


def test_summarize_tool_result_for_extract():
    payload = {
        "results": [
            {
                "url": "https://example.com/page",
                "raw_content": "long page " * 500,
            }
        ],
        "failed_results": [],
    }
    summary = summarize_tool_result_for_agent("tavily_extract", payload)
    assert "tavily_extract" in summary
    assert "https://example.com/page" in summary
    assert "原文约" in summary
    assert "预览:" in summary
    assert len(summary) <= 5000
