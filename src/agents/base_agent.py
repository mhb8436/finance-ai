"""Base agent class for all FinanceAI agents."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from src.core.config import get_llm_config
from src.services.llm import complete, stream, LLMResponse


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """Initialize the base agent.

        Args:
            model: LLM model to use. Defaults to config value.
            temperature: Temperature for generation. Defaults to config value.
            max_tokens: Max tokens for generation. Defaults to config value.
        """
        llm_config = get_llm_config()

        self.model = model or llm_config["model"]
        self.temperature = temperature if temperature is not None else llm_config["temperature"]
        self.max_tokens = max_tokens or llm_config["max_tokens"]

    async def call_llm(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Call the LLM and return the response content.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools for function calling (OpenAI format).

        Returns:
            The assistant's response text.
        """
        response = await self.call_llm_with_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        return response.content

    async def call_llm_with_response(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Call the LLM and return the full response object.

        Use this method when you need access to tool calls or other response metadata.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools for function calling (OpenAI format).

        Returns:
            Full LLMResponse with content, tool_calls, usage, etc.
        """
        return await complete(
            messages=messages,
            model=self.model,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            tools=tools,
        )

    async def stream_llm(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream LLM response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.

        Yields:
            Response text chunks.
        """
        async for chunk in stream(
            messages=messages,
            model=self.model,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        ):
            yield chunk

    @abstractmethod
    async def process(self, *args, **kwargs) -> dict[str, Any]:
        """Process the agent's main task. Must be implemented by subclasses."""
        pass
