"""Test Web Search functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestSearchTypes:
    """Test web search data types."""

    def test_search_result_dataclass(self):
        """Test SearchResult dataclass."""
        from src.tools.web_search import SearchResult

        result = SearchResult(
            title="Test Article",
            url="https://example.com/article",
            snippet="This is a test article snippet.",
            source="duckduckgo",
            published="2025-01-20",
        )

        assert result.title == "Test Article"
        assert result.url == "https://example.com/article"
        assert result.snippet == "This is a test article snippet."
        assert result.source == "duckduckgo"
        assert result.published == "2025-01-20"
        assert result.metadata is None

    def test_search_result_to_dict(self):
        """Test SearchResult.to_dict method."""
        from src.tools.web_search import SearchResult

        result = SearchResult(
            title="Test",
            url="https://test.com",
            snippet="Test snippet",
            source="google_news",
            metadata={"key": "value"},
        )

        d = result.to_dict()
        assert d["title"] == "Test"
        assert d["url"] == "https://test.com"
        assert d["snippet"] == "Test snippet"
        assert d["source"] == "google_news"
        assert d["metadata"] == {"key": "value"}

    def test_search_result_to_text(self):
        """Test SearchResult.to_text method."""
        from src.tools.web_search import SearchResult

        result = SearchResult(
            title="Test Article",
            url="https://test.com",
            snippet="Test content here",
            source="duckduckgo",
            published="2025-01-20",
        )

        text = result.to_text()
        assert "제목: Test Article" in text
        assert "URL: https://test.com" in text
        assert "출처: duckduckgo" in text
        assert "날짜: 2025-01-20" in text
        assert "내용: Test content here" in text


class TestSearchProviders:
    """Test individual search providers."""

    @pytest.mark.asyncio
    async def test_search_duckduckgo(self):
        """Test DuckDuckGo search function structure."""
        from src.tools.web_search import search_duckduckgo

        # Mock the duckduckgo_search module (imported inside the function)
        mock_ddgs_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {
                "title": "Test Result",
                "href": "https://example.com",
                "body": "Test body text",
            }
        ]
        mock_ddgs_class.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("sys.modules", {"duckduckgo_search": MagicMock(DDGS=mock_ddgs_class)}):
            # Reload to pick up the mock
            import importlib
            import src.tools.web_search as ws

            # The function imports DDGS inside, so we mock the module
            with patch("duckduckgo_search.DDGS", mock_ddgs_class):
                results = await search_duckduckgo("test query", max_results=5)

                assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_google_news_rss(self):
        """Test Google News RSS search function."""
        from src.tools.web_search import search_google_news_rss

        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
        <channel>
            <item>
                <title>Google News Article - Test Source</title>
                <link>https://news.google.com/article</link>
                <description>Article description</description>
                <pubDate>Mon, 20 Jan 2025 12:00:00 GMT</pubDate>
            </item>
        </channel>
        </rss>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = rss_content.encode()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    get=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            results = await search_google_news_rss("test", max_results=5)

            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0].title == "Google News Article"
            assert results[0].source == "google_news"

    @pytest.mark.asyncio
    async def test_search_serper(self):
        """Test Serper search function."""
        from src.tools.web_search import search_serper

        mock_response_data = {
            "organic": [
                {
                    "title": "Serper Result",
                    "link": "https://serper.com/result",
                    "snippet": "Serper snippet",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.dict(os.environ, {"SEARCH_API_KEY": "test-key"}):
                results = await search_serper("test query", max_results=5)

            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0].title == "Serper Result"
            assert results[0].source == "serper"

    @pytest.mark.asyncio
    async def test_search_tavily(self):
        """Test Tavily search function."""
        from src.tools.web_search import search_tavily

        mock_response_data = {
            "results": [
                {
                    "title": "Tavily Result",
                    "url": "https://tavily.com/result",
                    "content": "Tavily content",
                    "score": 0.95,
                }
            ],
            "answer": "AI-generated answer",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.dict(os.environ, {"SEARCH_API_KEY": "test-key"}):
                results, answer = await search_tavily("test query", max_results=5, topic="finance")

            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0].title == "Tavily Result"
            assert results[0].source == "tavily"
            assert answer == "AI-generated answer"

    @pytest.mark.asyncio
    async def test_search_serper_no_api_key(self):
        """Test Serper returns empty list when no API key."""
        from src.tools.web_search import search_serper

        with patch.dict(os.environ, {"SEARCH_API_KEY": ""}, clear=True):
            results = await search_serper("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_tavily_no_api_key(self):
        """Test Tavily returns empty list when no API key."""
        from src.tools.web_search import search_tavily

        with patch.dict(os.environ, {"SEARCH_API_KEY": ""}, clear=True):
            results, answer = await search_tavily("test query")
            assert results == []
            assert answer == ""


class TestWebSearchFunction:
    """Test main web_search function."""

    @pytest.mark.asyncio
    async def test_web_search_specific_providers(self):
        """Test web_search with specific providers."""
        from src.tools.web_search import web_search, SearchResult

        mock_result = SearchResult(
            title="DDG Result",
            url="https://ddg.com",
            snippet="DDG snippet",
            source="duckduckgo",
        )

        with patch(
            "src.tools.web_search.search_duckduckgo",
            AsyncMock(return_value=[mock_result]),
        ):
            results = await web_search("test query", providers=["duckduckgo"])

            assert len(results) == 1
            assert results[0].source == "duckduckgo"

    @pytest.mark.asyncio
    async def test_web_search_with_tavily(self):
        """Test web_search with tavily provider."""
        from src.tools.web_search import web_search, SearchResult

        mock_tavily_results = [
            SearchResult(
                title="Tavily Result",
                url="https://tavily.com",
                snippet="Tavily content",
                source="tavily",
            )
        ]

        with patch(
            "src.tools.web_search.search_tavily",
            AsyncMock(return_value=(mock_tavily_results, "Answer")),
        ):
            results = await web_search("test query", providers=["tavily"], topic="finance")

            assert len(results) == 1
            assert results[0].source == "tavily"


class TestSearchFinanceNews:
    """Test search_finance_news function."""

    @pytest.mark.asyncio
    async def test_search_finance_news_with_api_key(self):
        """Test finance news search with premium providers."""
        from src.tools.web_search import search_finance_news, SearchResult

        mock_results = [
            SearchResult(
                title="Finance Article",
                url="https://finance.com",
                snippet="Finance content",
                source="tavily",
            ),
        ]

        with patch.dict(os.environ, {"SEARCH_API_KEY": "test-key"}), patch(
            "src.tools.web_search.web_search",
            AsyncMock(return_value=mock_results),
        ):
            result = await search_finance_news("AAPL stock", max_results=5)

            assert result["success"] is True
            assert result["results_count"] == 1
            assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_finance_news_fallback(self):
        """Test finance news search fallback to free providers."""
        from src.tools.web_search import search_finance_news, SearchResult

        mock_results = [
            SearchResult(
                title="News Article",
                url="https://news.com",
                snippet="News content",
                source="google_news",
            ),
        ]

        with patch.dict(os.environ, {"SEARCH_API_KEY": ""}, clear=True), patch(
            "src.tools.web_search.web_search",
            AsyncMock(return_value=mock_results),
        ):
            result = await search_finance_news("AAPL stock", max_results=5)

            assert result["success"] is True


class TestExecuteWebSearchTool:
    """Test execute_web_search_tool function."""

    @pytest.mark.asyncio
    async def test_execute_web_search_tool_basic(self):
        """Test executing web search tool."""
        from src.tools.web_search import execute_web_search_tool, SearchResult

        mock_results = [
            SearchResult(
                title="Result 1",
                url="https://test.com",
                snippet="Snippet",
                source="duckduckgo",
            ),
        ]

        with patch(
            "src.tools.web_search.web_search",
            AsyncMock(return_value=mock_results),
        ):
            result = await execute_web_search_tool(
                query="test query",
                providers=["duckduckgo"],
                max_results=5,
            )

            assert result["success"] is True
            assert result["query"] == "test query"
            assert result["results_count"] == 1


class TestToolRouterIntegration:
    """Test ToolRouter integration with web search."""

    def test_tool_type_enum_has_web_search(self):
        """Test ToolType enum includes web search types."""
        from src.services.tool_router.types import ToolType

        assert hasattr(ToolType, "WEB_SEARCH")
        assert hasattr(ToolType, "NEWS_SEARCH")
        assert hasattr(ToolType, "FINANCE_NEWS")

        assert ToolType.WEB_SEARCH.value == "web_search"
        assert ToolType.NEWS_SEARCH.value == "news_search"
        assert ToolType.FINANCE_NEWS.value == "finance_news"

    def test_tool_router_has_handlers(self):
        """Test ToolRouter registers web search handlers."""
        from src.services.tool_router import ToolRouter

        router = ToolRouter()
        available_tools = router.get_available_tools()

        assert "web_search" in available_tools
        assert "news_search" in available_tools
        assert "finance_news" in available_tools

    @pytest.mark.asyncio
    async def test_tool_router_execute_web_search(self):
        """Test executing web_search via ToolRouter."""
        from src.services.tool_router import ToolRouter, ToolStatus
        from src.tools.web_search import SearchResult

        mock_results = [
            SearchResult(
                title="Test Result",
                url="https://test.com",
                snippet="Test snippet",
                source="duckduckgo",
            ),
        ]

        with patch(
            "src.tools.web_search.web_search",
            AsyncMock(return_value=mock_results),
        ):
            router = ToolRouter()
            result = await router.execute(
                "web_search",
                query="test query",
                providers=["duckduckgo"],
                max_results=5,
            )

            assert result.status == ToolStatus.SUCCESS
            assert result.data is not None
            assert result.data["query"] == "test query"
            assert result.data["count"] == 1

    @pytest.mark.asyncio
    async def test_tool_router_execute_finance_news(self):
        """Test executing finance_news via ToolRouter."""
        from src.services.tool_router import ToolRouter, ToolStatus

        mock_result = {
            "success": True,
            "results_count": 2,
            "results": [
                {"title": "Article 1", "url": "https://a.com", "snippet": "S1"},
                {"title": "Article 2", "url": "https://b.com", "snippet": "S2"},
            ],
        }

        with patch(
            "src.tools.web_search.search_finance_news",
            AsyncMock(return_value=mock_result),
        ):
            router = ToolRouter()
            result = await router.execute(
                "finance_news",
                query="Apple earnings",
                max_results=10,
            )

            assert result.status == ToolStatus.SUCCESS
            assert result.data is not None


class TestToolDefinitions:
    """Test tool definitions for LLM function calling."""

    def test_web_search_tool_definitions_exist(self):
        """Test WEB_SEARCH_TOOL_DEFINITIONS is properly defined."""
        from src.tools.web_search import WEB_SEARCH_TOOL_DEFINITIONS

        assert isinstance(WEB_SEARCH_TOOL_DEFINITIONS, list)
        assert len(WEB_SEARCH_TOOL_DEFINITIONS) >= 2  # web_search and search_finance_news

    def test_web_search_tool_definition_schema(self):
        """Test web_search tool definition has correct schema."""
        from src.tools.web_search import WEB_SEARCH_TOOL_DEFINITIONS

        web_search_def = next(
            (t for t in WEB_SEARCH_TOOL_DEFINITIONS if t["function"]["name"] == "web_search"),
            None,
        )

        assert web_search_def is not None
        assert web_search_def["type"] == "function"

        func = web_search_def["function"]
        assert "description" in func
        assert "parameters" in func

        params = func["parameters"]
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "query" in params["required"]
        assert "topic" in params["properties"]

    def test_finance_news_tool_definition_schema(self):
        """Test search_finance_news tool definition has correct schema."""
        from src.tools.web_search import WEB_SEARCH_TOOL_DEFINITIONS

        finance_def = next(
            (
                t
                for t in WEB_SEARCH_TOOL_DEFINITIONS
                if t["function"]["name"] == "search_finance_news"
            ),
            None,
        )

        assert finance_def is not None
        func = finance_def["function"]
        assert "description" in func
        assert "parameters" in func

    def test_tool_functions_mapping(self):
        """Test WEB_SEARCH_TOOL_FUNCTIONS mapping."""
        from src.tools.web_search import WEB_SEARCH_TOOL_FUNCTIONS

        assert "web_search" in WEB_SEARCH_TOOL_FUNCTIONS
        assert "search_finance_news" in WEB_SEARCH_TOOL_FUNCTIONS
        assert callable(WEB_SEARCH_TOOL_FUNCTIONS["web_search"])
        assert callable(WEB_SEARCH_TOOL_FUNCTIONS["search_finance_news"])


class TestNaverSearchClient:
    """Test Naver Search API client."""

    def test_naver_client_init(self):
        """Test NaverSearchClient initialization."""
        from src.tools.web_search import NaverSearchClient

        # Without credentials
        with patch.dict(os.environ, {"NAVER_CLIENT_ID": "", "NAVER_CLIENT_SECRET": ""}, clear=True):
            client = NaverSearchClient()
            assert not client.is_configured

        # With credentials
        client = NaverSearchClient(
            client_id="test_id",
            client_secret="test_secret",
        )
        assert client.is_configured

    @pytest.mark.asyncio
    async def test_naver_client_not_configured(self):
        """Test Naver client returns empty when not configured."""
        from src.tools.web_search import search_naver

        with patch.dict(os.environ, {"NAVER_CLIENT_ID": "", "NAVER_CLIENT_SECRET": ""}, clear=True):
            results = await search_naver("test query")
            assert results == []


class TestUtilityFunctions:
    """Test utility functions."""

    def test_strip_html(self):
        """Test HTML stripping function."""
        from src.tools.web_search import _strip_html

        # Test HTML tag removal
        assert _strip_html("<b>bold</b>") == "bold"
        assert _strip_html("<p>paragraph</p>") == "paragraph"

        # Test HTML entity decoding
        assert _strip_html("&lt;test&gt;") == "<test>"
        assert _strip_html("&amp;") == "&"
        assert _strip_html("&quot;") == '"'

        # Test whitespace normalization
        assert _strip_html("  multiple   spaces  ") == "multiple spaces"

        # Test empty input
        assert _strip_html("") == ""
        assert _strip_html(None) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
