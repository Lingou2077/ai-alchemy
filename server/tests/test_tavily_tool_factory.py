from unittest.mock import patch

from services.research.tavily_tool_factory import build_tavily_tools, use_mock_tavily


def test_use_mock_when_no_api_key():
    with patch("services.research.tavily_tool_factory.settings.tavily_api_key", ""):
        with patch("services.research.tavily_tool_factory.settings.tavily_mock", False):
            assert use_mock_tavily() is True


def test_use_mock_when_tavily_mock_enabled():
    with patch("services.research.tavily_tool_factory.settings.tavily_api_key", "tvly-test"):
        with patch("services.research.tavily_tool_factory.settings.tavily_mock", True):
            assert use_mock_tavily() is True


def test_use_real_when_key_and_mock_disabled():
    with patch("services.research.tavily_tool_factory.settings.tavily_api_key", "tvly-test"):
        with patch("services.research.tavily_tool_factory.settings.tavily_mock", False):
            assert use_mock_tavily() is False


def test_build_mock_tools_when_mock_mode():
    with patch("services.research.tavily_tool_factory.use_mock_tavily", return_value=True):
        tools = build_tavily_tools()
    names = {t.name for t in tools}
    assert names == {"tavily_search", "tavily_extract"}
