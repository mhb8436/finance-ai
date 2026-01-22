"""News search tools for stock-related news."""

import os
from typing import Any
from datetime import datetime


async def search_news(
    query: str,
    market: str = "US",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search for news about a stock or topic.

    Args:
        query: Search query (stock symbol or topic)
        market: Market code
        limit: Maximum number of results

    Returns:
        List of news articles.
    """
    # Try different news sources based on availability
    search_key = os.getenv("SEARCH_API_KEY")
    search_provider = os.getenv("SEARCH_PROVIDER", "")

    if search_provider == "serper" and search_key:
        return await _search_serper(query, market, limit, search_key)

    # Fallback to yfinance news
    return await _search_yfinance_news(query, market, limit)


async def _search_yfinance_news(
    query: str,
    market: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Get news from yfinance."""
    import yfinance as yf

    # Try to get news for the symbol
    symbol = query.upper()
    if market == "KR" and not symbol.endswith(".KS"):
        symbol = f"{symbol}.KS"

    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news

        results = []
        for item in news[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "source": item.get("publisher", ""),
                "date": datetime.fromtimestamp(
                    item.get("providerPublishTime", 0)
                ).strftime("%Y-%m-%d") if item.get("providerPublishTime") else "",
                "summary": item.get("summary", ""),
            })

        return results

    except Exception as e:
        print(f"Error fetching yfinance news: {e}")
        return []


async def _search_serper(
    query: str,
    market: str,
    limit: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Search news using Serper API."""
    import httpx

    # Add market-specific context to query
    if market == "KR":
        search_query = f"{query} 주식 뉴스"
    else:
        search_query = f"{query} stock news"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/news",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": search_query,
                    "num": limit,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("news", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", ""),
                    "summary": item.get("snippet", ""),
                })

            return results

    except Exception as e:
        print(f"Error searching news with Serper: {e}")
        return []


async def get_market_news(market: str = "US", limit: int = 10) -> list[dict[str, Any]]:
    """Get general market news.

    Args:
        market: Market code
        limit: Maximum results

    Returns:
        List of market news articles.
    """
    if market == "KR":
        query = "KOSPI KOSDAQ 증시"
    else:
        query = "S&P 500 NASDAQ stock market"

    return await search_news(query, market, limit)
