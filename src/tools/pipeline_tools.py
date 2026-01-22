"""Pipeline Tool Integration.

Provides pre-configured tool handlers for the ResearchPipeline.
Combines all available tools (stock, financials, RAG, web search, YouTube)
into a unified interface.

Usage:
    from src.tools.pipeline_tools import get_pipeline_tool_handlers
    from src.agents.research import ResearchPipeline

    pipeline = ResearchPipeline()
    handlers = get_pipeline_tool_handlers()

    for name, handler in handlers.items():
        pipeline.register_tool(name, handler)
"""

import json
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


# =============================================================================
# Stock Data Tool Handler
# =============================================================================


async def stock_data_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle stock data queries.

    Args:
        query: Query string (may contain symbol or be a general query).
        symbols: List of symbols to query.

    Returns:
        JSON string with stock data.
    """
    from src.tools.stock_data import get_stock_info, get_stock_price

    try:
        results = {}

        # Use provided symbols or extract from query
        target_symbols = symbols or []
        if not target_symbols and query:
            # Simple extraction: assume query might be a symbol
            query_upper = query.upper().strip()
            if len(query_upper) <= 10 and query_upper.isalnum():
                target_symbols = [query_upper]

        if not target_symbols:
            return json.dumps({"error": "No symbols provided"})

        for symbol in target_symbols[:5]:  # Limit to 5 symbols
            try:
                # Determine market from symbol
                market = "KR" if symbol.isdigit() else "US"

                info = await get_stock_info(symbol, market)
                price = await get_stock_price(symbol, market, period="1mo", interval="1d")

                results[symbol] = {
                    "info": info,
                    "recent_price": price[-5:] if price else [],
                }
            except Exception as e:
                results[symbol] = {"error": str(e)}

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Stock data error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Financials Tool Handler
# =============================================================================


async def financials_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle financial data queries.

    Args:
        query: Query string.
        symbols: List of symbols to query.

    Returns:
        JSON string with financial data.
    """
    from src.tools.financials import get_financial_statements, get_financial_ratios

    try:
        results = {}

        target_symbols = symbols or []
        if not target_symbols and query:
            query_upper = query.upper().strip()
            if len(query_upper) <= 10 and query_upper.isalnum():
                target_symbols = [query_upper]

        if not target_symbols:
            return json.dumps({"error": "No symbols provided"})

        for symbol in target_symbols[:3]:  # Limit to 3 symbols
            try:
                market = "KR" if symbol.isdigit() else "US"

                statements = await get_financial_statements(symbol, market)
                ratios = await get_financial_ratios(symbol, market)

                results[symbol] = {
                    "statements": statements,
                    "ratios": ratios,
                }
            except Exception as e:
                results[symbol] = {"error": str(e)}

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Financials error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Technical Analysis Tool Handler
# =============================================================================


async def technical_analysis_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle technical analysis queries.

    Args:
        query: Query string.
        symbols: List of symbols to analyze.

    Returns:
        JSON string with technical indicators.
    """
    from src.tools.stock_data import get_stock_price
    from src.tools.indicators import (
        calculate_sma,
        calculate_ema,
        calculate_rsi,
        calculate_macd,
        calculate_bollinger_bands,
    )

    try:
        results = {}

        target_symbols = symbols or []
        if not target_symbols:
            return json.dumps({"error": "No symbols provided"})

        for symbol in target_symbols[:3]:
            try:
                market = "KR" if symbol.isdigit() else "US"
                price_data = await get_stock_price(symbol, market, period="6mo", interval="1d")

                if not price_data:
                    results[symbol] = {"error": "No price data"}
                    continue

                # Extract close prices
                closes = [p.get("close", 0) for p in price_data if p.get("close")]

                if len(closes) < 20:
                    results[symbol] = {"error": "Insufficient data"}
                    continue

                # Calculate indicators
                sma_20 = calculate_sma(closes, 20)
                sma_50 = calculate_sma(closes, 50)
                ema_12 = calculate_ema(closes, 12)
                rsi = calculate_rsi(closes, 14)
                macd_result = calculate_macd(closes)
                bb = calculate_bollinger_bands(closes, 20)

                results[symbol] = {
                    "current_price": closes[-1] if closes else None,
                    "sma_20": sma_20[-1] if sma_20 else None,
                    "sma_50": sma_50[-1] if sma_50 else None,
                    "ema_12": ema_12[-1] if ema_12 else None,
                    "rsi_14": rsi[-1] if rsi else None,
                    "macd": {
                        "macd": macd_result["macd"][-1] if macd_result.get("macd") else None,
                        "signal": macd_result["signal"][-1] if macd_result.get("signal") else None,
                        "histogram": macd_result["histogram"][-1] if macd_result.get("histogram") else None,
                    },
                    "bollinger": {
                        "upper": bb["upper"][-1] if bb.get("upper") else None,
                        "middle": bb["middle"][-1] if bb.get("middle") else None,
                        "lower": bb["lower"][-1] if bb.get("lower") else None,
                    },
                    "data_points": len(closes),
                }

            except Exception as e:
                results[symbol] = {"error": str(e)}

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# RAG Search Tool Handler
# =============================================================================


async def rag_search_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle RAG knowledge base queries.

    Args:
        query: Search query.
        symbols: Optional symbols for context.

    Returns:
        JSON string with search results.
    """
    from src.tools.rag_tool import search_knowledge_base

    try:
        # Enhance query with symbols if provided
        enhanced_query = query
        if symbols:
            enhanced_query = f"{query} {' '.join(symbols)}"

        result = await search_knowledge_base(
            query=enhanced_query,
            kb_name=kwargs.get("kb_name", "default"),
            top_k=kwargs.get("top_k", 5),
        )

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Web Search Tool Handler
# =============================================================================


async def web_search_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle web search queries.

    Args:
        query: Search query.
        symbols: Optional symbols for context.

    Returns:
        JSON string with search results.
    """
    from src.tools.web_search import web_search

    try:
        # Enhance query with symbols
        enhanced_query = query
        if symbols:
            enhanced_query = f"{query} {' '.join(symbols[:2])}"  # Limit symbols in query

        results = await web_search(
            query=enhanced_query,
            providers=kwargs.get("providers", ["duckduckgo", "google_news"]),
            max_results=kwargs.get("max_results", 10),
        )

        return json.dumps({
            "success": True,
            "query": enhanced_query,
            "results_count": len(results),
            "results": [r.to_dict() for r in results[:15]],
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# News Search Tool Handler
# =============================================================================


async def news_search_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle news search queries.

    Args:
        query: Search query.
        symbols: Optional symbols for context.

    Returns:
        JSON string with news results.
    """
    from src.tools.web_search import search_duckduckgo_news, search_google_news_rss
    import asyncio

    try:
        # Enhance query with symbols
        enhanced_query = query
        if symbols:
            enhanced_query = f"{query} {' '.join(symbols[:2])}"

        # Search both news sources
        ddg_task = search_duckduckgo_news(enhanced_query, max_results=5)
        google_task = search_google_news_rss(enhanced_query, max_results=5)

        ddg_results, google_results = await asyncio.gather(
            ddg_task, google_task, return_exceptions=True
        )

        all_results = []
        if isinstance(ddg_results, list):
            all_results.extend(ddg_results)
        if isinstance(google_results, list):
            all_results.extend(google_results)

        return json.dumps({
            "success": True,
            "query": enhanced_query,
            "results_count": len(all_results),
            "results": [r.to_dict() for r in all_results[:10]],
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"News search error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# YouTube Tool Handler
# =============================================================================


async def youtube_handler(
    query: str,
    symbols: list[str] | None = None,
    **kwargs,
) -> str:
    """Handle YouTube transcript queries.

    Args:
        query: Video URL, channel name, or search query.
        symbols: Optional symbols for context.

    Returns:
        JSON string with YouTube results.
    """
    from src.tools.youtube_tool import (
        get_transcript,
        get_channel_videos,
        extract_video_id,
        KOREAN_INVESTMENT_CHANNELS,
    )

    try:
        # Check if query is a video URL/ID
        video_id = extract_video_id(query)
        if video_id:
            transcript = await get_transcript(video_id)
            if transcript:
                return json.dumps({
                    "success": True,
                    "type": "transcript",
                    **transcript.to_dict(),
                    "text_preview": transcript.text[:3000] + "..." if len(transcript.text) > 3000 else transcript.text,
                }, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": "Could not get transcript",
                })

        # Check if query is a preset channel name
        if query in KOREAN_INVESTMENT_CHANNELS:
            videos = await get_channel_videos(query, max_results=10)
            return json.dumps({
                "success": True,
                "type": "channel_videos",
                "channel": query,
                "video_count": len(videos),
                "videos": [v.to_dict() for v in videos],
            }, ensure_ascii=False, indent=2)

        # General: return available channels
        return json.dumps({
            "success": True,
            "type": "info",
            "message": "Provide a video URL or channel name",
            "available_channels": list(KOREAN_INVESTMENT_CHANNELS.keys()),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"YouTube error: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Tool Registry
# =============================================================================


def get_pipeline_tool_handlers() -> dict[str, Callable[..., Awaitable[str]]]:
    """Get all available tool handlers for the ResearchPipeline.

    Returns:
        Dictionary mapping tool names to handler functions.
    """
    return {
        "stock_data": stock_data_handler,
        "financials": financials_handler,
        "technical_analysis": technical_analysis_handler,
        "rag_search": rag_search_handler,
        "web_search": web_search_handler,
        "news_search": news_search_handler,
        "youtube": youtube_handler,
    }


def get_tool_descriptions() -> str:
    """Get descriptions of all available tools.

    Returns:
        Formatted string with tool descriptions.
    """
    return """Available Research Tools:
- stock_data: Get stock price data and company information
- financials: Get financial statements and ratios
- technical_analysis: Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger)
- rag_search: Search uploaded documents and knowledge base
- web_search: Search the web (DuckDuckGo, Google News)
- news_search: Search recent news articles
- youtube: Get YouTube video transcripts and channel videos"""


# =============================================================================
# Convenience Functions
# =============================================================================


def create_configured_pipeline(
    model: str | None = None,
    state_dir: str | None = None,
    **kwargs,
):
    """Create a ResearchPipeline with all tools pre-registered.

    Args:
        model: LLM model to use.
        state_dir: Directory for state persistence.
        **kwargs: Additional pipeline arguments.

    Returns:
        Configured ResearchPipeline instance.
    """
    from src.agents.research import ResearchPipeline

    pipeline = ResearchPipeline(
        model=model,
        state_dir=state_dir,
        **kwargs,
    )

    # Register all tools
    handlers = get_pipeline_tool_handlers()
    descriptions = {
        "stock_data": "Get stock price data and company information",
        "financials": "Get financial statements and ratios",
        "technical_analysis": "Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger)",
        "rag_search": "Search uploaded documents and knowledge base",
        "web_search": "Search the web for information",
        "news_search": "Search recent news articles",
        "youtube": "Get YouTube video transcripts and channel videos",
    }

    for name, handler in handlers.items():
        pipeline.register_tool(name, handler, descriptions.get(name))

    # Set tools description for the research agent
    pipeline._research_agent.set_tools_description(get_tool_descriptions())

    return pipeline


async def quick_research(
    topic: str,
    symbols: list[str] | None = None,
    market: str = "US",
    **kwargs,
) -> dict[str, Any]:
    """Convenience function for quick research.

    Args:
        topic: Research topic.
        symbols: Stock symbols.
        market: Target market.
        **kwargs: Additional arguments.

    Returns:
        Research results.
    """
    pipeline = create_configured_pipeline(**kwargs)
    return await pipeline.run(
        topic=topic,
        symbols=symbols,
        market=market,
    )
