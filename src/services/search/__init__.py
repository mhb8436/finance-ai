"""Web Search Service.

Provides unified web search across multiple providers:
- Serper (Google SERP)
- Tavily (Research-focused with AI answers)

Example:
    from src.services.search import web_search

    # Simple search
    result = await web_search("What is quantum computing?")
    print(result["answer"])

    # With specific provider
    result = await web_search(
        "Latest AI news",
        provider="tavily",
        topic="news",
    )
"""

import logging
import os
from typing import Any

from .base import BaseSearchProvider
from .providers import get_available_providers, get_provider, list_providers
from .types import Citation, SearchResult, WebSearchResponse

logger = logging.getLogger(__name__)

# Default provider
DEFAULT_PROVIDER = "serper"


async def web_search(
    query: str,
    provider: str | None = None,
    max_results: int = 10,
    api_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Perform a web search using the specified provider.

    This is the main entry point for web search functionality.

    Args:
        query: Search query.
        provider: Provider name (serper, tavily). Defaults to env/config.
        max_results: Maximum results to return.
        api_key: Optional API key override.
        **kwargs: Provider-specific parameters.

    Returns:
        Dictionary with search results and optional answer.
        Keys: query, answer, provider, citations, search_results, timestamp, metadata

    Raises:
        ValueError: If provider not found or not available.

    Examples:
        # Basic search
        result = await web_search("What is machine learning?")

        # News search with Serper
        result = await web_search(
            "Tesla stock news",
            provider="serper",
            search_type="news",
        )

        # Research search with Tavily
        result = await web_search(
            "Climate change impact on agriculture",
            provider="tavily",
            search_depth="advanced",
            topic="general",
        )

        # Finance-focused search
        result = await web_search(
            "Apple quarterly earnings",
            provider="tavily",
            topic="finance",
        )
    """
    # Determine provider
    if provider is None:
        provider = os.getenv("SEARCH_PROVIDER", DEFAULT_PROVIDER)

    # Get provider instance
    search_provider = get_provider(provider, api_key=api_key)

    if not search_provider.is_available():
        available = get_available_providers(api_key)
        if available:
            logger.warning(
                f"Provider {provider} not available, falling back to {available[0]}"
            )
            search_provider = get_provider(available[0], api_key=api_key)
        else:
            raise ValueError(
                f"No search providers available. Set SEARCH_API_KEY environment variable."
            )

    # Perform search
    logger.info(f"Searching with {search_provider.name}: {query[:50]}...")
    response = await search_provider.search(query, max_results=max_results, **kwargs)

    return response.to_dict()


def get_search_config() -> dict[str, Any]:
    """Get current search configuration.

    Returns:
        Dictionary with configuration details.
    """
    provider = os.getenv("SEARCH_PROVIDER", DEFAULT_PROVIDER)
    has_key = bool(os.getenv("SEARCH_API_KEY"))

    return {
        "default_provider": provider,
        "api_key_configured": has_key,
        "available_providers": list_providers(),
        "active_providers": get_available_providers() if has_key else [],
    }


__all__ = [
    # Main function
    "web_search",
    "get_search_config",
    # Types
    "Citation",
    "SearchResult",
    "WebSearchResponse",
    # Provider utilities
    "BaseSearchProvider",
    "get_provider",
    "list_providers",
    "get_available_providers",
]
