import json

from langchain_core.tools import StructuredTool

from services.research.input_classifier import extract_urls

_MOCK_SEARCH_FIXTURE = {
    "query": "",
    "results": [
        {
            "title": "Harness Engineering - AI Agent Methodology",
            "url": "https://example.com/harness-engineering-ai",
            "content": (
                "Harness Engineering refers to an AI-assisted software engineering "
                "methodology for building reliable agent workflows with evaluation harnesses."
            ),
            "score": 0.92,
        },
        {
            "title": "Mechanical Harness Systems",
            "url": "https://example.com/mechanical-harness",
            "content": "Industrial harness systems connect cables and safety equipment in vehicles.",
            "score": 0.71,
        },
    ],
}

_MOCK_EXTRACT_FIXTURE = {
    "results": [
        {
            "url": "https://en.wikipedia.org/wiki/Lionel_Messi",
            "raw_content": "Lionel Messi is an Argentine professional footballer widely regarded as one of the greatest players.",
        }
    ],
    "failed_results": [],
}


def _mock_tavily_search(query: str, **kwargs: object) -> str:
    payload = dict(_MOCK_SEARCH_FIXTURE)
    payload["query"] = query
    return json.dumps(payload, ensure_ascii=False)


def _mock_tavily_extract(urls: list[str], **kwargs: object) -> str:
    url = urls[0] if urls else "https://example.com/page"
    payload = {
        "results": [
            {
                "url": url,
                "raw_content": f"Mock extracted page content from {url}. This article explains the topic in detail.",
            }
        ],
        "failed_results": [],
    }
    return json.dumps(payload, ensure_ascii=False)


def build_mock_tavily_tools() -> list[StructuredTool]:
    search_tool = StructuredTool.from_function(
        func=_mock_tavily_search,
        name="tavily_search",
        description="Search the web for up-to-date information about a topic.",
    )
    extract_tool = StructuredTool.from_function(
        func=_mock_tavily_extract,
        name="tavily_extract",
        description="Extract full page content from one or more URLs.",
    )
    return [search_tool, extract_tool]


def mock_auto_materials(content: str) -> tuple[str, str | None]:
    urls = extract_urls(content)
    if urls:
        return "tavily_extract", json.dumps(
            _mock_tavily_extract([urls[0]]),
            ensure_ascii=False,
        )
    return "tavily_search", json.dumps(
        {**_MOCK_SEARCH_FIXTURE, "query": content[:120]},
        ensure_ascii=False,
    )
