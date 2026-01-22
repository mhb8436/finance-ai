"""Base class for search providers."""

import os
from abc import ABC, abstractmethod
from typing import Any

from .types import WebSearchResponse


class BaseSearchProvider(ABC):
    """Abstract base class for search providers."""

    # Provider metadata (override in subclasses)
    name: str = "base"
    display_name: str = "Base Provider"
    description: str = "Base search provider"
    supports_answer: bool = False
    requires_api_key: bool = True

    def __init__(self, api_key: str | None = None):
        """Initialize the provider.

        Args:
            api_key: API key for the provider. Falls back to SEARCH_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SEARCH_API_KEY", "")

    def is_available(self) -> bool:
        """Check if the provider is available (has API key).

        Returns:
            True if provider can be used.
        """
        if not self.requires_api_key:
            return True
        return bool(self.api_key)

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs: Any,
    ) -> WebSearchResponse:
        """Perform a web search.

        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Provider-specific parameters.

        Returns:
            WebSearchResponse with results and optional answer.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, available={self.is_available()})"
