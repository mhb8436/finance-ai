"""Tool Router - Unified tool execution with retry and timeout.

Based on DeepTutor's research_pipeline._call_tool_with_retry pattern.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Coroutine

from .types import ToolConfig, ToolResult, ToolStatus, ToolType, ToolTrace

logger = logging.getLogger(__name__)


class ToolRouter:
    """Unified tool router with retry, timeout, and error handling.

    Example:
        router = ToolRouter()

        # Execute single tool
        result = await router.execute(
            tool_type="stock_price",
            symbol="AAPL",
            market="US",
        )

        # Execute multiple tools in parallel
        results = await router.execute_parallel([
            {"tool_type": "stock_price", "symbol": "AAPL"},
            {"tool_type": "stock_info", "symbol": "AAPL"},
            {"tool_type": "news_search", "query": "AAPL stock"},
        ])
    """

    def __init__(self, config: ToolConfig | None = None):
        """Initialize ToolRouter.

        Args:
            config: Tool configuration. Uses defaults if not provided.
        """
        self.config = config or ToolConfig()
        self._handlers: dict[str, Callable[..., Coroutine[Any, Any, dict]]] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all tool handlers."""
        # Stock tools
        self._handlers[ToolType.STOCK_PRICE.value] = self._handle_stock_price
        self._handlers[ToolType.STOCK_INFO.value] = self._handle_stock_info
        self._handlers[ToolType.FINANCIAL_RATIOS.value] = self._handle_financial_ratios
        self._handlers[ToolType.TECHNICAL_INDICATORS.value] = self._handle_technical_indicators

        # Search tools
        self._handlers[ToolType.NEWS_SEARCH.value] = self._handle_news_search
        self._handlers[ToolType.WEB_SEARCH.value] = self._handle_web_search
        self._handlers[ToolType.FINANCE_NEWS.value] = self._handle_finance_news

        # RAG tools
        self._handlers[ToolType.RAG_SEARCH.value] = self._handle_rag_search

        # YouTube tools
        self._handlers[ToolType.YOUTUBE_TRANSCRIPT.value] = self._handle_youtube_transcript
        self._handlers[ToolType.YOUTUBE_CHANNEL.value] = self._handle_youtube_channel

    async def execute(
        self,
        tool_type: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool with retry and timeout.

        Args:
            tool_type: Type of tool to execute.
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with status and data.
        """
        start_time = time.time()
        query = {"tool_type": tool_type, **kwargs}

        # Check if handler exists
        handler = self._handlers.get(tool_type)
        if not handler:
            return ToolResult(
                tool_type=tool_type,
                query=query,
                status=ToolStatus.FAILED,
                error=f"Unknown tool type: {tool_type}",
                execution_time=time.time() - start_time,
            )

        # Execute with retry
        result = await self._execute_with_retry(
            handler=handler,
            tool_type=tool_type,
            query=query,
            kwargs=kwargs,
        )

        result.execution_time = time.time() - start_time
        return result

    async def _execute_with_retry(
        self,
        handler: Callable[..., Coroutine[Any, Any, dict]],
        tool_type: str,
        query: dict[str, Any],
        kwargs: dict[str, Any],
    ) -> ToolResult:
        """Execute handler with retry logic.

        Args:
            handler: Tool handler function.
            tool_type: Type of tool.
            query: Query parameters for logging.
            kwargs: Parameters to pass to handler.

        Returns:
            ToolResult with status and data.
        """
        last_error = None
        retries = 0

        for attempt in range(self.config.max_retries + 1):
            try:
                # Execute with timeout
                data = await asyncio.wait_for(
                    handler(**kwargs),
                    timeout=self.config.timeout,
                )

                # Check if data is valid
                if data is None:
                    raise ValueError("Handler returned None")

                # Success
                status = ToolStatus.RETRIED if retries > 0 else ToolStatus.SUCCESS
                return ToolResult(
                    tool_type=tool_type,
                    query=query,
                    status=status,
                    data=data,
                    retries=retries,
                )

            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout}s"
                logger.warning(
                    f"Tool {tool_type} timeout (attempt {attempt + 1}/{self.config.max_retries + 1})"
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Tool {tool_type} error (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}"
                )

            # Increment retry count and wait before next attempt
            retries += 1
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)

        # All retries failed
        return ToolResult(
            tool_type=tool_type,
            query=query,
            status=ToolStatus.TIMEOUT if "Timeout" in (last_error or "") else ToolStatus.FAILED,
            error=last_error,
            retries=retries,
        )

    async def execute_parallel(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel.

        Args:
            tool_calls: List of tool call specifications.
                Each dict must have 'tool_type' and tool-specific params.

        Returns:
            List of ToolResults in same order as input.
        """
        tasks = []
        for call in tool_calls:
            tool_type = call.pop("tool_type", None)
            if tool_type:
                tasks.append(self.execute(tool_type, **call))
            else:
                # Return error result for invalid call
                tasks.append(self._create_error_result(call, "Missing tool_type"))

        return await asyncio.gather(*tasks)

    async def _create_error_result(
        self,
        query: dict[str, Any],
        error: str,
    ) -> ToolResult:
        """Create error result without execution."""
        return ToolResult(
            tool_type="unknown",
            query=query,
            status=ToolStatus.FAILED,
            error=error,
        )

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _handle_stock_price(
        self,
        symbol: str,
        market: str = "US",
        period: str = "1mo",
        interval: str = "1d",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle stock price tool."""
        from src.tools.stock_data import get_stock_price

        prices = await get_stock_price(symbol, market, period, interval)

        if not prices:
            raise ValueError(f"No price data for {symbol}")

        return {
            "symbol": symbol,
            "market": market,
            "period": period,
            "prices": prices,
            "latest": prices[-1] if prices else None,
        }

    async def _handle_stock_info(
        self,
        symbol: str,
        market: str = "US",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle stock info tool."""
        from src.tools.stock_data import get_stock_info

        info = await get_stock_info(symbol, market)

        if not info or info.get("name") == "Unknown":
            raise ValueError(f"No info for {symbol}")

        return info

    async def _handle_financial_ratios(
        self,
        symbol: str,
        market: str = "US",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle financial ratios tool."""
        from src.tools.financials import get_financial_ratios

        ratios = await get_financial_ratios(symbol, market)

        if not ratios:
            raise ValueError(f"No financial ratios for {symbol}")

        return ratios

    async def _handle_technical_indicators(
        self,
        symbol: str,
        market: str = "US",
        period: str = "3mo",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle technical indicators tool."""
        from src.tools.indicators import calculate_indicators
        from src.tools.stock_data import get_stock_price

        # Get price data first
        prices = await get_stock_price(symbol, market, period, "1d")

        if not prices:
            raise ValueError(f"No price data for {symbol}")

        # Calculate indicators
        indicators = await calculate_indicators(prices)

        return {
            "symbol": symbol,
            "market": market,
            "indicators": indicators,
        }

    async def _handle_news_search(
        self,
        query: str,
        market: str = "US",
        limit: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle news search tool."""
        from src.tools.news_search import search_news

        articles = await search_news(query, market, limit)

        return {
            "query": query,
            "market": market,
            "articles": articles,
            "count": len(articles),
        }

    async def _handle_web_search(
        self,
        query: str,
        providers: list[str] | None = None,
        max_results: int = 10,
        topic: str = "general",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle web search tool."""
        from src.tools.web_search import web_search

        results = await web_search(query, providers, max_results, topic=topic)

        return {
            "query": query,
            "providers": providers or ["duckduckgo", "google_news"],
            "topic": topic,
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }

    async def _handle_finance_news(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle finance news search tool."""
        from src.tools.web_search import search_finance_news

        result = await search_finance_news(query, max_results)

        return result

    async def _handle_rag_search(
        self,
        query: str,
        kb_name: str = "default",
        top_k: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle RAG search tool."""
        from src.tools.rag_tool import search_knowledge_base

        result = await search_knowledge_base(query, kb_name, top_k)

        return result

    async def _handle_youtube_transcript(
        self,
        video_url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle YouTube transcript tool."""
        from src.tools.youtube_tool import get_transcript

        transcript = await get_transcript(video_url)

        if not transcript:
            raise ValueError(f"Could not get transcript for {video_url}")

        return {
            "video_id": transcript.video_id,
            "title": transcript.title,
            "channel_name": transcript.channel_name,
            "language": transcript.language,
            "duration_seconds": transcript.duration_seconds,
            "text": transcript.text[:10000],  # Limit size
        }

    async def _handle_youtube_channel(
        self,
        channel: str,
        max_results: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle YouTube channel videos tool."""
        from src.tools.youtube_tool import get_channel_videos

        videos = await get_channel_videos(channel, max_results)

        return {
            "channel": channel,
            "videos": [v.to_dict() for v in videos],
            "count": len(videos),
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def create_trace(
        self,
        result: ToolResult,
        summary: str | None = None,
        citation_id: str | None = None,
    ) -> ToolTrace:
        """Create a tool trace for reporting.

        Args:
            result: Tool execution result.
            summary: Optional summary of the result.
            citation_id: Optional citation ID.

        Returns:
            ToolTrace object.
        """
        return ToolTrace(
            tool_id=str(uuid.uuid4())[:8],
            tool_type=result.tool_type,
            query=result.query,
            raw_result=result,
            summary=summary,
            citation_id=citation_id,
        )

    def get_available_tools(self) -> list[str]:
        """Get list of available tool types."""
        return list(self._handlers.keys())


# Global instance
_tool_router: ToolRouter | None = None


def get_tool_router(config: ToolConfig | None = None) -> ToolRouter:
    """Get or create the global ToolRouter instance.

    Args:
        config: Optional configuration. Only used on first call.

    Returns:
        Global ToolRouter instance.
    """
    global _tool_router

    if _tool_router is None:
        _tool_router = ToolRouter(config)

    return _tool_router
