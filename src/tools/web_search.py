"""Web Search Tools.

Provides multiple web search providers:
1. DuckDuckGo (free, no API key)
2. Naver API (free tier, requires API key)
3. Google News RSS (free, no API key)
4. Serper (Google SERP, requires API key)
5. Tavily (AI-powered, requires API key)
"""

import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote, urlencode

import httpx


@dataclass
class SearchResult:
    """Unified search result format."""

    title: str
    url: str
    snippet: str
    source: str  # duckduckgo, naver, google_news
    published: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "published": self.published,
            "metadata": self.metadata or {},
        }

    def to_text(self) -> str:
        """Convert to text for RAG indexing."""
        parts = [
            f"제목: {self.title}",
            f"URL: {self.url}",
            f"출처: {self.source}",
        ]
        if self.published:
            parts.append(f"날짜: {self.published}")
        parts.append(f"내용: {self.snippet}")
        return "\n".join(parts)


# =============================================================================
# 1. DuckDuckGo Search (무료, API 키 불필요)
# =============================================================================


async def search_duckduckgo(
    query: str,
    max_results: int = 10,
    region: str = "kr-kr",
) -> list[SearchResult]:
    """Search using DuckDuckGo.

    Args:
        query: Search query.
        max_results: Maximum number of results.
        region: Region code (kr-kr for Korea).

    Returns:
        List of SearchResult objects.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError(
            "duckduckgo-search is required. Install with: pip install duckduckgo-search"
        )

    results: list[SearchResult] = []

    try:
        # Run in thread pool since DDGS is synchronous
        def _search():
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        query,
                        region=region,
                        max_results=max_results,
                    )
                )

        raw_results = await asyncio.to_thread(_search)

        for item in raw_results:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    metadata={"region": region},
                )
            )

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")

    return results


async def search_duckduckgo_news(
    query: str,
    max_results: int = 10,
    region: str = "kr-kr",
) -> list[SearchResult]:
    """Search news using DuckDuckGo.

    Args:
        query: Search query.
        max_results: Maximum number of results.
        region: Region code.

    Returns:
        List of SearchResult objects.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError(
            "duckduckgo-search is required. Install with: pip install duckduckgo-search"
        )

    results: list[SearchResult] = []

    try:
        def _search():
            with DDGS() as ddgs:
                return list(
                    ddgs.news(
                        query,
                        region=region,
                        max_results=max_results,
                    )
                )

        raw_results = await asyncio.to_thread(_search)

        for item in raw_results:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo_news",
                    published=item.get("date"),
                    metadata={
                        "region": region,
                        "source_name": item.get("source"),
                    },
                )
            )

    except Exception as e:
        print(f"DuckDuckGo news search error: {e}")

    return results


# =============================================================================
# 2. Naver Search API (무료 25,000건/일)
# =============================================================================


class NaverSearchClient:
    """Naver Search API client.

    Requires NAVER_CLIENT_ID and NAVER_CLIENT_SECRET environment variables.
    Register at: https://developers.naver.com/
    """

    BASE_URL = "https://openapi.naver.com/v1/search"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        import os

        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _request(
        self,
        endpoint: str,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim",  # sim: 정확도, date: 날짜순
    ) -> dict[str, Any]:
        """Make API request to Naver."""
        if not self.is_configured:
            return {"items": []}

        url = f"{self.BASE_URL}/{endpoint}"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def search_news(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search Naver News.

        Args:
            query: Search query.
            max_results: Maximum number of results.

        Returns:
            List of SearchResult objects.
        """
        results: list[SearchResult] = []

        try:
            data = await self._request("news.json", query, display=max_results)

            for item in data.get("items", []):
                # Clean HTML tags from title and description
                title = _strip_html(item.get("title", ""))
                snippet = _strip_html(item.get("description", ""))

                results.append(
                    SearchResult(
                        title=title,
                        url=item.get("link", ""),
                        snippet=snippet,
                        source="naver_news",
                        published=item.get("pubDate"),
                        metadata={
                            "original_link": item.get("originallink"),
                        },
                    )
                )

        except Exception as e:
            print(f"Naver news search error: {e}")

        return results

    async def search_blog(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search Naver Blog.

        Args:
            query: Search query.
            max_results: Maximum number of results.

        Returns:
            List of SearchResult objects.
        """
        results: list[SearchResult] = []

        try:
            data = await self._request("blog.json", query, display=max_results)

            for item in data.get("items", []):
                title = _strip_html(item.get("title", ""))
                snippet = _strip_html(item.get("description", ""))

                results.append(
                    SearchResult(
                        title=title,
                        url=item.get("link", ""),
                        snippet=snippet,
                        source="naver_blog",
                        published=item.get("postdate"),
                        metadata={
                            "blogger_name": item.get("bloggername"),
                            "blogger_link": item.get("bloggerlink"),
                        },
                    )
                )

        except Exception as e:
            print(f"Naver blog search error: {e}")

        return results

    async def search_cafe(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search Naver Cafe.

        Args:
            query: Search query.
            max_results: Maximum number of results.

        Returns:
            List of SearchResult objects.
        """
        results: list[SearchResult] = []

        try:
            data = await self._request("cafearticle.json", query, display=max_results)

            for item in data.get("items", []):
                title = _strip_html(item.get("title", ""))
                snippet = _strip_html(item.get("description", ""))

                results.append(
                    SearchResult(
                        title=title,
                        url=item.get("link", ""),
                        snippet=snippet,
                        source="naver_cafe",
                        metadata={
                            "cafe_name": item.get("cafename"),
                            "cafe_url": item.get("cafeurl"),
                        },
                    )
                )

        except Exception as e:
            print(f"Naver cafe search error: {e}")

        return results


async def search_naver(
    query: str,
    search_type: str = "news",  # news, blog, cafe
    max_results: int = 10,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> list[SearchResult]:
    """Search using Naver API.

    Args:
        query: Search query.
        search_type: Type of search (news, blog, cafe).
        max_results: Maximum number of results.
        client_id: Naver API client ID.
        client_secret: Naver API client secret.

    Returns:
        List of SearchResult objects.
    """
    client = NaverSearchClient(client_id, client_secret)

    if not client.is_configured:
        print("Naver API not configured. Set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET.")
        return []

    if search_type == "news":
        return await client.search_news(query, max_results)
    elif search_type == "blog":
        return await client.search_blog(query, max_results)
    elif search_type == "cafe":
        return await client.search_cafe(query, max_results)
    else:
        return await client.search_news(query, max_results)


# =============================================================================
# 3. Google News RSS (무료, API 키 불필요)
# =============================================================================


async def search_google_news_rss(
    query: str,
    max_results: int = 10,
    language: str = "ko",
    country: str = "KR",
) -> list[SearchResult]:
    """Search Google News via RSS feed.

    Args:
        query: Search query.
        max_results: Maximum number of results.
        language: Language code (ko, en, etc.).
        country: Country code (KR, US, etc.).

    Returns:
        List of SearchResult objects.
    """
    results: list[SearchResult] = []

    # Build RSS URL
    encoded_query = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Find all items in the RSS feed
            items = root.findall(".//item")

            for item in items[:max_results]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                description = item.findtext("description", "")

                # Clean description (often contains HTML)
                snippet = _strip_html(description)

                # Extract source from title (usually "Title - Source")
                source_name = ""
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source_name = parts[1]

                results.append(
                    SearchResult(
                        title=title,
                        url=link,
                        snippet=snippet,
                        source="google_news",
                        published=pub_date,
                        metadata={
                            "source_name": source_name,
                            "language": language,
                            "country": country,
                        },
                    )
                )

    except Exception as e:
        print(f"Google News RSS error: {e}")

    return results


# =============================================================================
# 4. Serper (Google SERP - requires API key)
# =============================================================================


async def search_serper(
    query: str,
    max_results: int = 10,
    search_type: str = "search",  # search, news
    gl: str = "us",
    hl: str = "en",
) -> list[SearchResult]:
    """Search using Serper.dev (Google SERP).

    Args:
        query: Search query.
        max_results: Maximum number of results.
        search_type: Type of search (search, news).
        gl: Country code.
        hl: Language code.

    Returns:
        List of SearchResult objects.
    """
    import os

    api_key = os.getenv("SEARCH_API_KEY", "")
    if not api_key:
        return []

    results: list[SearchResult] = []

    try:
        endpoint = f"https://google.serper.dev/{search_type}"
        payload = {"q": query, "num": max_results, "gl": gl, "hl": hl}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Parse organic results
        for item in data.get("organic", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serper",
                    published=item.get("date"),
                    metadata={
                        "position": item.get("position"),
                        "sitelinks": item.get("sitelinks", []),
                    },
                )
            )

        # Parse news results if present
        for item in data.get("news", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serper_news",
                    published=item.get("date"),
                    metadata={"source_name": item.get("source")},
                )
            )

    except Exception as e:
        print(f"Serper search error: {e}")

    return results


# =============================================================================
# 5. Tavily (AI-powered search - requires API key)
# =============================================================================


async def search_tavily(
    query: str,
    max_results: int = 10,
    search_depth: str = "basic",  # basic or advanced
    topic: str = "general",  # general, news, finance
    include_answer: bool = True,
) -> tuple[list[SearchResult], str]:
    """Search using Tavily API.

    Args:
        query: Search query.
        max_results: Maximum number of results.
        search_depth: Search depth (basic or advanced).
        topic: Topic filter (general, news, finance).
        include_answer: Whether to include AI-generated answer.

    Returns:
        Tuple of (List of SearchResult, AI answer string).
    """
    import os

    api_key = os.getenv("SEARCH_API_KEY", "")
    if not api_key:
        return [], ""

    results: list[SearchResult] = []
    answer = ""

    try:
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
            "include_answer": include_answer,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        answer = data.get("answer", "")

        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="tavily",
                    metadata={
                        "score": item.get("score"),
                        "published_date": item.get("published_date"),
                    },
                )
            )

    except Exception as e:
        print(f"Tavily search error: {e}")

    return results, answer


# =============================================================================
# Unified Search Interface
# =============================================================================


async def web_search(
    query: str,
    providers: list[str] | None = None,
    max_results: int = 10,
    **kwargs: Any,
) -> list[SearchResult]:
    """Unified web search across multiple providers.

    Args:
        query: Search query.
        providers: List of providers to use. Default: ["duckduckgo", "google_news"]
                   Options: duckduckgo, duckduckgo_news, naver_news, naver_blog,
                            naver_cafe, google_news, serper, serper_news, tavily
        max_results: Maximum results per provider.
        **kwargs: Provider-specific options (e.g., topic for tavily).

    Returns:
        Combined list of SearchResult objects.
    """
    if providers is None:
        providers = ["duckduckgo", "google_news"]

    all_results: list[SearchResult] = []
    tasks = []
    tavily_providers = []  # Handle tavily separately due to answer

    for provider in providers:
        if provider == "duckduckgo":
            tasks.append(search_duckduckgo(query, max_results))
        elif provider == "duckduckgo_news":
            tasks.append(search_duckduckgo_news(query, max_results))
        elif provider == "naver_news":
            tasks.append(search_naver(query, "news", max_results))
        elif provider == "naver_blog":
            tasks.append(search_naver(query, "blog", max_results))
        elif provider == "naver_cafe":
            tasks.append(search_naver(query, "cafe", max_results))
        elif provider == "google_news":
            tasks.append(search_google_news_rss(query, max_results))
        elif provider == "serper":
            tasks.append(search_serper(query, max_results, search_type="search"))
        elif provider == "serper_news":
            tasks.append(search_serper(query, max_results, search_type="news"))
        elif provider == "tavily":
            tavily_providers.append(provider)

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                print(f"Search error: {result}")

    # Handle Tavily separately (returns tuple with answer)
    for provider in tavily_providers:
        try:
            topic = kwargs.get("topic", "general")
            tavily_results, _ = await search_tavily(
                query, max_results, topic=topic
            )
            all_results.extend(tavily_results)
        except Exception as e:
            print(f"Tavily search error: {e}")

    return all_results


# =============================================================================
# RAG Integration
# =============================================================================


async def search_and_store_to_rag(
    query: str,
    kb_name: str = "web_search",
    providers: list[str] | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """Search and store results in RAG knowledge base.

    Args:
        query: Search query.
        kb_name: Knowledge base name to store results.
        providers: List of search providers.
        max_results: Maximum results per provider.

    Returns:
        Dictionary with search stats and stored chunks.
    """
    from src.services.rag import get_rag_service
    from src.services.rag.types import Chunk

    # Perform search
    results = await web_search(query, providers, max_results)

    if not results:
        return {
            "success": False,
            "message": "No search results found",
            "results_count": 0,
        }

    # Convert to chunks
    chunks: list[Chunk] = []
    for i, result in enumerate(results):
        chunk = Chunk(
            content=result.to_text(),
            chunk_type="web_search",
            metadata={
                "title": result.title,
                "url": result.url,
                "source": result.source,
                "published": result.published,
                "query": query,
                "chunk_index": i,
                **(result.metadata or {}),
            },
        )
        chunks.append(chunk)

    # Store in RAG
    service = get_rag_service()
    retriever = service._get_or_create_retriever(kb_name)
    await retriever.add_chunks(chunks)

    return {
        "success": True,
        "query": query,
        "kb_name": kb_name,
        "results_count": len(results),
        "providers_used": providers or ["duckduckgo", "google_news"],
        "results": [r.to_dict() for r in results],
    }


# =============================================================================
# Utility Functions
# =============================================================================


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re

    if not text:
        return ""

    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    clean = clean.replace("&lt;", "<")
    clean = clean.replace("&gt;", ">")
    clean = clean.replace("&amp;", "&")
    clean = clean.replace("&quot;", '"')
    clean = clean.replace("&#39;", "'")
    clean = clean.replace("&nbsp;", " ")
    # Clean whitespace
    clean = " ".join(clean.split())

    return clean


# =============================================================================
# Tool Definitions for Agent
# =============================================================================


WEB_SEARCH_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for information. Supports multiple providers: "
                "DuckDuckGo (general web, free), Google News (news, free), "
                "Naver (Korean content), Serper (Google SERP), Tavily (AI-powered). "
                "Use this to find recent news, articles, or information about stocks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Search providers to use. Options: duckduckgo, "
                            "duckduckgo_news, naver_news, naver_blog, google_news, "
                            "serper, serper_news, tavily. "
                            "Default: ['duckduckgo', 'google_news']"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results per provider. Default: 10",
                        "default": 10,
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["general", "news", "finance"],
                        "description": "Topic filter for Tavily. Default: general",
                        "default": "general",
                    },
                    "store_to_rag": {
                        "type": "boolean",
                        "description": "Whether to store results in RAG knowledge base.",
                        "default": False,
                    },
                    "kb_name": {
                        "type": "string",
                        "description": "Knowledge base name if storing to RAG.",
                        "default": "web_search",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_finance_news",
            "description": (
                "Search for financial news and stock market information. "
                "Optimized for finding recent news about stocks, companies, and markets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'Tesla earnings', 'AAPL stock news').",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return. Default: 10",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


async def execute_web_search_tool(
    query: str,
    providers: list[str] | None = None,
    max_results: int = 10,
    topic: str = "general",
    store_to_rag: bool = False,
    kb_name: str = "web_search",
) -> dict[str, Any]:
    """Execute web search tool for agent.

    Args:
        query: Search query.
        providers: List of providers.
        max_results: Maximum results.
        topic: Topic filter for Tavily.
        store_to_rag: Whether to store in RAG.
        kb_name: Knowledge base name.

    Returns:
        Search results dictionary.
    """
    if store_to_rag:
        return await search_and_store_to_rag(
            query=query,
            kb_name=kb_name,
            providers=providers,
            max_results=max_results,
        )
    else:
        results = await web_search(query, providers, max_results, topic=topic)
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": [r.to_dict() for r in results[:20]],  # Limit for response
        }


async def search_finance_news(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    """Search for financial news.

    Uses multiple providers optimized for financial content.

    Args:
        query: Search query about stocks or finance.
        max_results: Maximum results.

    Returns:
        Search results dictionary.
    """
    import os

    # Use best available provider for finance
    providers = ["google_news", "duckduckgo_news"]

    # Add premium providers if API key available
    if os.getenv("SEARCH_API_KEY"):
        providers = ["tavily", "serper_news"] + providers

    results = await web_search(query, providers, max_results, topic="finance")

    return {
        "success": True,
        "query": query,
        "results_count": len(results),
        "results": [r.to_dict() for r in results[:max_results]],
    }


# Function mapping for tool calls
WEB_SEARCH_TOOL_FUNCTIONS = {
    "web_search": execute_web_search_tool,
    "search_finance_news": search_finance_news,
}
