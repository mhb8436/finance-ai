"""Web Search API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class WebSearchRequest(BaseModel):
    query: str
    providers: list[str] | None = None  # duckduckgo, google_news, naver_news, serper, tavily, etc.
    max_results: int = 10
    topic: str = "general"  # general, news, finance (for tavily)
    store_to_rag: bool = False
    kb_name: str = "web_search"


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published: str | None = None
    metadata: dict[str, Any] = {}


class WebSearchResponse(BaseModel):
    success: bool
    query: str
    results_count: int
    results: list[SearchResultItem]
    stored_to_rag: bool = False
    kb_name: str | None = None


@router.post("/web")
async def web_search(request: WebSearchRequest) -> WebSearchResponse:
    """Search the web using multiple providers.

    Providers:
    - duckduckgo: General web search (free, no API key)
    - duckduckgo_news: News search via DuckDuckGo
    - google_news: Google News RSS feed (free, no API key)
    - naver_news: Naver News (requires NAVER_CLIENT_ID/SECRET)
    - naver_blog: Naver Blog search
    - naver_cafe: Naver Cafe search
    - serper: Google SERP via Serper.dev (requires SEARCH_API_KEY)
    - serper_news: Google News via Serper.dev
    - tavily: AI-powered research search (requires SEARCH_API_KEY)
    """
    try:
        from src.tools.web_search import (
            web_search as do_web_search,
            search_and_store_to_rag,
        )

        if request.store_to_rag:
            result = await search_and_store_to_rag(
                query=request.query,
                kb_name=request.kb_name,
                providers=request.providers,
                max_results=request.max_results,
            )

            return WebSearchResponse(
                success=result.get("success", False),
                query=request.query,
                results_count=result.get("results_count", 0),
                results=[
                    SearchResultItem(**r) for r in result.get("results", [])
                ],
                stored_to_rag=True,
                kb_name=request.kb_name,
            )
        else:
            results = await do_web_search(
                query=request.query,
                providers=request.providers,
                max_results=request.max_results,
                topic=request.topic,
            )

            return WebSearchResponse(
                success=True,
                query=request.query,
                results_count=len(results),
                results=[
                    SearchResultItem(
                        title=r.title,
                        url=r.url,
                        snippet=r.snippet,
                        source=r.source,
                        published=r.published,
                        metadata=r.metadata or {},
                    )
                    for r in results
                ],
                stored_to_rag=False,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers() -> dict[str, Any]:
    """List available search providers and their status."""
    import os

    naver_configured = bool(
        os.getenv("NAVER_CLIENT_ID") and os.getenv("NAVER_CLIENT_SECRET")
    )
    search_api_configured = bool(os.getenv("SEARCH_API_KEY"))

    return {
        "providers": [
            {
                "id": "duckduckgo",
                "name": "DuckDuckGo Web",
                "type": "web",
                "requires_api_key": False,
                "available": True,
            },
            {
                "id": "duckduckgo_news",
                "name": "DuckDuckGo News",
                "type": "news",
                "requires_api_key": False,
                "available": True,
            },
            {
                "id": "google_news",
                "name": "Google News RSS",
                "type": "news",
                "requires_api_key": False,
                "available": True,
            },
            {
                "id": "naver_news",
                "name": "Naver News",
                "type": "news",
                "requires_api_key": True,
                "available": naver_configured,
            },
            {
                "id": "naver_blog",
                "name": "Naver Blog",
                "type": "blog",
                "requires_api_key": True,
                "available": naver_configured,
            },
            {
                "id": "naver_cafe",
                "name": "Naver Cafe",
                "type": "community",
                "requires_api_key": True,
                "available": naver_configured,
            },
            {
                "id": "serper",
                "name": "Serper (Google SERP)",
                "type": "web",
                "requires_api_key": True,
                "available": search_api_configured,
            },
            {
                "id": "serper_news",
                "name": "Serper News",
                "type": "news",
                "requires_api_key": True,
                "available": search_api_configured,
            },
            {
                "id": "tavily",
                "name": "Tavily (AI-powered)",
                "type": "research",
                "requires_api_key": True,
                "available": search_api_configured,
                "features": ["ai_answer", "finance_topic"],
            },
        ],
        "default_providers": ["duckduckgo", "google_news"],
    }


@router.post("/finance")
async def search_finance_news(
    query: str,
    max_results: int = 10,
) -> WebSearchResponse:
    """Search for financial news and stock market information.

    Optimized for finding recent news about stocks, companies, and markets.
    Uses Tavily (if available) or falls back to free providers.
    """
    try:
        from src.tools.web_search import search_finance_news as do_finance_search

        result = await do_finance_search(query=query, max_results=max_results)

        return WebSearchResponse(
            success=result.get("success", False),
            query=query,
            results_count=result.get("results_count", 0),
            results=[SearchResultItem(**r) for r in result.get("results", [])],
            stored_to_rag=False,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
