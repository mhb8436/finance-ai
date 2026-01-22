"""Tavily search provider - Research-focused search with AI answers."""

import logging
from typing import Any

import httpx

from ..base import BaseSearchProvider
from ..types import Citation, SearchResult, WebSearchResponse
from . import register_provider

logger = logging.getLogger(__name__)


@register_provider("tavily")
class TavilyProvider(BaseSearchProvider):
    """Tavily search provider for research-focused search with AI answers."""

    name = "tavily"
    display_name = "Tavily"
    description = "Research-focused search with AI-generated answers"
    supports_answer = True
    requires_api_key = True

    BASE_URL = "https://api.tavily.com"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",  # basic or advanced
        topic: str = "general",  # general, news, finance
        include_answer: bool = True,
        include_raw_content: bool = False,
        days: int | None = None,  # For news: limit to recent days
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        **kwargs: Any,
    ) -> WebSearchResponse:
        """Search using Tavily API.

        Args:
            query: Search query.
            max_results: Maximum results to return.
            search_depth: Search depth (basic or advanced).
            topic: Topic filter (general, news, finance).
            include_answer: Whether to include AI-generated answer.
            include_raw_content: Whether to include full page content.
            days: Limit results to recent N days (for news).
            include_domains: Only include these domains.
            exclude_domains: Exclude these domains.
            **kwargs: Additional parameters.

        Returns:
            WebSearchResponse with search results and answer.
        """
        if not self.is_available():
            raise ValueError("Tavily API key not configured")

        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }

        if days is not None:
            payload["days"] = days
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(query, data)

    def _parse_response(
        self,
        query: str,
        data: dict[str, Any],
    ) -> WebSearchResponse:
        """Parse Tavily API response.

        Args:
            query: Original query.
            data: API response data.

        Returns:
            Parsed WebSearchResponse.
        """
        citations: list[Citation] = []
        search_results: list[SearchResult] = []
        metadata: dict[str, Any] = {}

        # Extract answer
        answer = data.get("answer", "")

        # Extract results
        results = data.get("results", [])
        for i, item in enumerate(results):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source=self._extract_domain(item.get("url", "")),
                content=item.get("raw_content", ""),
                score=item.get("score"),
                metadata={
                    "published_date": item.get("published_date"),
                },
            )
            search_results.append(result)

            citation = Citation(
                id=i + 1,
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source=self._extract_domain(item.get("url", "")),
                content=item.get("raw_content", ""),
            )
            citations.append(citation)

        # Extract metadata
        if "images" in data:
            metadata["images"] = data["images"]
        if "response_time" in data:
            metadata["response_time"] = data["response_time"]

        # If no answer provided, create from results
        if not answer and search_results:
            answer = self._summarize_results(query, search_results[:5])

        return WebSearchResponse(
            query=query,
            answer=answer,
            provider=self.name,
            citations=citations,
            search_results=search_results,
            metadata=metadata,
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: Full URL.

        Returns:
            Domain name.
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    def _summarize_results(
        self,
        query: str,
        results: list[SearchResult],
    ) -> str:
        """Create a simple summary from search results.

        Args:
            query: Original query.
            results: Search results to summarize.

        Returns:
            Summary text.
        """
        if not results:
            return f"No results found for: {query}"

        lines = [f"Search results for '{query}':\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. **{result.title}**")
            if result.snippet:
                # Truncate long snippets
                snippet = result.snippet[:300] + "..." if len(result.snippet) > 300 else result.snippet
                lines.append(f"   {snippet}")
            lines.append(f"   Source: {result.source}\n")

        return "\n".join(lines)
