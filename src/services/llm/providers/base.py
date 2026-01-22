"""Base provider interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from ..types import LLMConfig, LLMResponse, ToolDefinition


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """Initialize the provider.

        Args:
            config: LLM configuration.
        """
        self.config = config
        self._client: Any = None

    @property
    @abstractmethod
    def client(self) -> Any:
        """Get the provider's client instance (lazy initialization)."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools for function calling.
            **kwargs: Additional provider-specific arguments.

        Returns:
            Unified LLMResponse.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            **kwargs: Additional provider-specific arguments.

        Yields:
            Response text chunks.
        """
        pass

    def _get_temperature(self, temperature: float | None) -> float:
        """Get temperature value, using config default if not provided."""
        return temperature if temperature is not None else self.config.temperature

    def _get_max_tokens(self, max_tokens: int | None) -> int:
        """Get max_tokens value, using config default if not provided."""
        return max_tokens or self.config.max_tokens
