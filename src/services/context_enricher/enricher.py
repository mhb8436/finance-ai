"""Context Enricher - Pre-fetch data based on query intent.

Based on DeepTutor's research_pipeline pattern:
- Analyze intent
- Determine required tools
- Execute tools in parallel
- Build enriched context for LLM
"""

import asyncio
import logging
from typing import Any

from src.services.intent_analyzer import (
    get_intent_analyzer,
    IntentType,
    QueryIntent,
    ExtractedSymbol,
)
from src.services.tool_router import get_tool_router, ToolResult

from .types import EnrichmentConfig, EnrichedContext

logger = logging.getLogger(__name__)


# Intent to tool mapping with priorities
INTENT_TOOL_PRIORITY: dict[IntentType, list[tuple[str, int]]] = {
    IntentType.STOCK_QUERY: [
        ("stock_price", 1),
        ("stock_info", 2),
        ("news_search", 3),
    ],
    IntentType.NEWS_QUERY: [
        ("news_search", 1),
        ("web_search", 2),
    ],
    IntentType.ANALYSIS_QUERY: [
        ("stock_price", 1),
        ("stock_info", 1),
        ("financial_ratios", 2),
        ("technical_indicators", 3),
    ],
    IntentType.COMPARISON_QUERY: [
        ("stock_price", 1),
        ("stock_info", 1),
        ("financial_ratios", 2),
    ],
    IntentType.GENERAL_QUERY: [],
}


class ContextEnricher:
    """Enrich query context by pre-fetching relevant data.

    Example:
        enricher = ContextEnricher()
        enriched = await enricher.enrich("삼성전자 주가 알려줘")

        print(enriched.context_string)  # Formatted context for LLM
        print(enriched.sources)  # Data sources used
    """

    def __init__(self, config: EnrichmentConfig | None = None) -> None:
        """Initialize ContextEnricher.

        Args:
            config: Enrichment configuration.
        """
        self.config = config or EnrichmentConfig()
        self._analyzer = get_intent_analyzer()
        self._router = get_tool_router()

    async def enrich(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> EnrichedContext:
        """Enrich query with pre-fetched data.

        Args:
            query: User's query string.
            context: Optional existing context (e.g., current symbol).

        Returns:
            EnrichedContext with pre-fetched data.
        """
        # Analyze intent
        intent = self._analyzer.analyze(query)

        # Skip enrichment for general queries
        if intent.intent_type == IntentType.GENERAL_QUERY:
            return EnrichedContext(intent=intent)

        # Skip if no symbols detected (except for news queries)
        if not intent.symbols and intent.intent_type != IntentType.NEWS_QUERY:
            return EnrichedContext(intent=intent)

        # Build tool calls based on intent
        tool_calls = self._build_tool_calls(intent)

        if not tool_calls:
            return EnrichedContext(intent=intent)

        # Execute tools in parallel
        tool_results = await self._execute_parallel(tool_calls)

        # Build context string
        context_string = self._build_context_string(tool_results)

        # Build sources
        sources = self._build_sources(tool_results)

        return EnrichedContext(
            intent=intent,
            tool_results=tool_results,
            context_string=context_string,
            sources=sources,
        )

    def _build_tool_calls(self, intent: QueryIntent) -> list[dict[str, Any]]:
        """Build tool call specifications based on intent.

        Args:
            intent: Analyzed query intent.

        Returns:
            List of tool call specifications.
        """
        tool_calls: list[dict[str, Any]] = []
        tools_priority = INTENT_TOOL_PRIORITY.get(intent.intent_type, [])

        # Limit symbols to process
        symbols = intent.symbols[: self.config.max_symbols]

        for symbol in symbols:
            market = symbol.market.value if symbol.market.value != "UNKNOWN" else "US"

            for tool_type, priority in tools_priority:
                call: dict[str, Any] = {"tool_type": tool_type, "_priority": priority}

                if tool_type == "stock_price":
                    call.update({
                        "symbol": symbol.symbol,
                        "market": market,
                        "period": "1mo",
                        "interval": "1d",
                    })
                elif tool_type == "stock_info":
                    call.update({
                        "symbol": symbol.symbol,
                        "market": market,
                    })
                elif tool_type == "financial_ratios":
                    call.update({
                        "symbol": symbol.symbol,
                        "market": market,
                    })
                elif tool_type == "technical_indicators":
                    call.update({
                        "symbol": symbol.symbol,
                        "market": market,
                        "period": "3mo",
                    })
                elif tool_type == "news_search":
                    if self.config.include_news_for_stock:
                        news_query = f"{symbol.company_name or symbol.symbol} stock news"
                        call.update({
                            "query": news_query,
                            "market": market,
                            "limit": self.config.news_limit,
                        })
                    else:
                        continue  # Skip news
                elif tool_type == "web_search":
                    search_query = f"{symbol.company_name or symbol.symbol} latest news"
                    call.update({
                        "query": search_query,
                        "max_results": self.config.news_limit,
                    })

                tool_calls.append(call)

        # Handle news query without symbols
        if not symbols and intent.intent_type == IntentType.NEWS_QUERY:
            # Use keywords for news search
            if intent.keywords:
                search_query = " ".join(intent.keywords[:3])
                tool_calls.append({
                    "tool_type": "news_search",
                    "query": search_query,
                    "limit": self.config.news_limit,
                    "_priority": 1,
                })

        # Sort by priority and limit
        tool_calls.sort(key=lambda x: x.get("_priority", 99))
        tool_calls = tool_calls[: self.config.max_parallel_calls]

        # Remove priority field
        for call in tool_calls:
            call.pop("_priority", None)

        return tool_calls

    async def _execute_parallel(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[ToolResult]:
        """Execute tool calls in parallel.

        Args:
            tool_calls: List of tool call specifications.

        Returns:
            List of ToolResult objects.
        """
        tasks = []

        for call in tool_calls:
            tool_type = call.pop("tool_type")
            tasks.append(self._router.execute(tool_type, **call))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results: list[ToolResult] = []
        for result in results:
            if isinstance(result, ToolResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Tool execution failed: {result}")

        return valid_results

    def _build_context_string(self, results: list[ToolResult]) -> str:
        """Build formatted context string for LLM.

        Args:
            results: List of tool results.

        Returns:
            Formatted context string.
        """
        if not results:
            return ""

        context_parts: list[str] = ["## Pre-fetched Data"]

        for result in results:
            if result.is_success and result.has_data:
                context_parts.append(result.to_context_string())

        if len(context_parts) == 1:  # Only header, no data
            return ""

        return "\n\n".join(context_parts)

    def _build_sources(self, results: list[ToolResult]) -> list[dict[str, Any]]:
        """Build sources list from tool results.

        Args:
            results: List of tool results.

        Returns:
            List of source dictionaries.
        """
        sources: list[dict[str, Any]] = []

        for result in results:
            source = {
                "type": result.tool_type,
                "status": result.status.value,
                "retries": result.retries,
                "execution_time": result.execution_time,
            }

            # Add query params
            for key in ["symbol", "market", "query"]:
                if key in result.query:
                    source[key] = result.query[key]

            sources.append(source)

        return sources


# Global instance
_context_enricher: ContextEnricher | None = None


def get_context_enricher(config: EnrichmentConfig | None = None) -> ContextEnricher:
    """Get or create global ContextEnricher instance.

    Args:
        config: Optional configuration. Only used on first call.

    Returns:
        Global ContextEnricher instance.
    """
    global _context_enricher

    if _context_enricher is None:
        _context_enricher = ContextEnricher(config)

    return _context_enricher
