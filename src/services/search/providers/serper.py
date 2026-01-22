"""Serper.dev search provider - Google SERP results."""

import logging
from typing import Any

import httpx

from ..base import BaseSearchProvider
from ..types import Citation, SearchResult, WebSearchResponse
from . import register_provider

logger = logging.getLogger(__name__)


@register_provider("serper")
class SerperProvider(BaseSearchProvider):
    """Serper.dev search provider for Google SERP results."""

    name = "serper"
    display_name = "Serper (Google)"
    description = "Google search results via serper.dev API"
    supports_answer = False  # Returns SERP, needs consolidation for answer
    requires_api_key = True

    BASE_URL = "https://google.serper.dev"

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "search",  # search, news, scholar
        gl: str = "us",  # Country
        hl: str = "en",  # Language
        **kwargs: Any,
    ) -> WebSearchResponse:
        """Search using Serper.dev API.

        Args:
            query: Search query.
            max_results: Maximum results to return.
            search_type: Type of search (search, news, scholar).
            gl: Country code for results.
            hl: Language code for results.
            **kwargs: Additional parameters.

        Returns:
            WebSearchResponse with search results.
        """
        if not self.is_available():
            raise ValueError("Serper API key not configured")

        endpoint = f"{self.BASE_URL}/{search_type}"

        payload = {
            "q": query,
            "num": max_results,
            "gl": gl,
            "hl": hl,
        }

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(query, data, search_type)

    def _parse_response(
        self,
        query: str,
        data: dict[str, Any],
        search_type: str,
    ) -> WebSearchResponse:
        """Parse Serper API response.

        Args:
            query: Original query.
            data: API response data.
            search_type: Type of search performed.

        Returns:
            Parsed WebSearchResponse.
        """
        citations: list[Citation] = []
        search_results: list[SearchResult] = []
        answer_parts: list[str] = []
        metadata: dict[str, Any] = {"search_type": search_type}

        # Extract answer box if present
        if "answerBox" in data:
            answer_box = data["answerBox"]
            if "answer" in answer_box:
                answer_parts.append(answer_box["answer"])
            elif "snippet" in answer_box:
                answer_parts.append(answer_box["snippet"])
            metadata["answer_box"] = answer_box

        # Extract knowledge graph if present
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            if "description" in kg:
                answer_parts.append(kg["description"])
            metadata["knowledge_graph"] = {
                "title": kg.get("title"),
                "type": kg.get("type"),
                "description": kg.get("description"),
            }

        # Extract organic results
        organic = data.get("organic", [])
        for i, item in enumerate(organic):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                date=item.get("date"),
                source=item.get("source", ""),
                metadata={
                    "position": item.get("position", i + 1),
                    "sitelinks": item.get("sitelinks", []),
                },
            )
            search_results.append(result)

            citation = Citation(
                id=i + 1,
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                date=item.get("date"),
                source=item.get("source", ""),
            )
            citations.append(citation)

        # Extract news results if present
        if "news" in data:
            for i, item in enumerate(data["news"]):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    date=item.get("date"),
                    source=item.get("source", ""),
                    metadata={"type": "news", "imageUrl": item.get("imageUrl")},
                )
                search_results.append(result)

        # Extract People Also Ask if present
        if "peopleAlsoAsk" in data:
            metadata["people_also_ask"] = [
                {"question": paa.get("question"), "snippet": paa.get("snippet")}
                for paa in data["peopleAlsoAsk"]
            ]

        # Extract related searches
        if "relatedSearches" in data:
            metadata["related_searches"] = [
                rs.get("query") for rs in data["relatedSearches"]
            ]

        # Build answer from extracted parts or summarize results
        if answer_parts:
            answer = "\n\n".join(answer_parts)
        else:
            # Create a simple summary from top results
            answer = self._summarize_results(query, search_results[:5])

        return WebSearchResponse(
            query=query,
            answer=answer,
            provider=self.name,
            citations=citations,
            search_results=search_results,
            metadata=metadata,
        )

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
                lines.append(f"   {result.snippet}")
            lines.append(f"   Source: {result.url}\n")

        return "\n".join(lines)
