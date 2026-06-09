from langchain_core.tools import BaseTool

from config import settings
from services.research.mock_tavily_tools import build_mock_tavily_tools


def use_mock_tavily() -> bool:
    return settings.tavily_mock or not settings.tavily_api_key.strip()


def build_tavily_tools() -> list[BaseTool]:
    if use_mock_tavily():
        return build_mock_tavily_tools()

    from langchain_tavily import TavilyExtract, TavilySearch

    api_key = settings.tavily_api_key
    search_tool = TavilySearch(
        max_results=settings.tavily_search_max_results,
        search_depth=settings.tavily_search_default_depth,
        topic="general",
        tavily_api_key=api_key,
    )
    extract_tool = TavilyExtract(
        extract_depth="basic",
        include_images=False,
        tavily_api_key=api_key,
    )
    return [search_tool, extract_tool]
