"""Anthropic provider implementation for Claude models."""

from typing import Any, AsyncIterator

from ..errors import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMContextLengthError,
    LLMRateLimitError,
)
from ..types import LLMConfig, LLMResponse, ToolCall, ToolDefinition
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude API."""

    @property
    def client(self) -> Any:
        """Get the Anthropic client (lazy initialization)."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required for Anthropic provider. "
                    "Install it with: pip install anthropic"
                )

            self._client = AsyncAnthropic(api_key=self.config.api_key)
        return self._client

    async def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools for function calling.
            **kwargs: Additional arguments.

        Returns:
            Unified LLMResponse.
        """
        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(self._convert_message(msg))

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": user_messages,
            "temperature": self._get_temperature(temperature),
            "max_tokens": self._get_max_tokens(max_tokens),
        }

        if system_message:
            request_kwargs["system"] = system_message

        if tools:
            request_kwargs["tools"] = [t.to_anthropic_format() for t in tools]

        request_kwargs.update(kwargs)

        try:
            response = await self.client.messages.create(**request_kwargs)
        except Exception as e:
            self._handle_error(e)

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        # Build usage dict
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "stop",
            usage=usage,
            raw_response=response,
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            **kwargs: Additional arguments.

        Yields:
            Response text chunks.
        """
        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(self._convert_message(msg))

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": user_messages,
            "temperature": self._get_temperature(temperature),
            "max_tokens": self._get_max_tokens(max_tokens),
        }

        if system_message:
            request_kwargs["system"] = system_message

        request_kwargs.update(kwargs)

        try:
            async with self.client.messages.stream(**request_kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            self._handle_error(e)

    def _convert_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Convert OpenAI-style message to Anthropic format.

        Args:
            msg: OpenAI-style message dict.

        Returns:
            Anthropic-style message dict.
        """
        role = msg["role"]
        content = msg.get("content", "")

        # Handle tool responses
        if role == "tool":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": content,
                    }
                ],
            }

        # Handle assistant messages with tool calls
        if role == "assistant" and msg.get("tool_calls"):
            blocks = []
            if content:
                blocks.append({"type": "text", "text": content})

            for tc in msg["tool_calls"]:
                if isinstance(tc, dict):
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": tc.get("function", {}).get("name", ""),
                        "input": tc.get("function", {}).get("arguments", {}),
                    })

            return {"role": "assistant", "content": blocks}

        # Standard message
        return {"role": role, "content": content}

    def _handle_error(self, error: Exception) -> None:
        """Convert Anthropic errors to LLM service errors."""
        try:
            from anthropic import (
                APIConnectionError,
                AuthenticationError,
                BadRequestError,
                RateLimitError,
            )
        except ImportError:
            raise error

        provider = "anthropic"

        if isinstance(error, AuthenticationError):
            raise LLMAuthenticationError(
                f"Authentication failed: {error}",
                provider=provider,
            )
        elif isinstance(error, RateLimitError):
            raise LLMRateLimitError(
                f"Rate limit exceeded: {error}",
                provider=provider,
            )
        elif isinstance(error, APIConnectionError):
            raise LLMConnectionError(
                f"Connection error: {error}",
                provider=provider,
            )
        elif isinstance(error, BadRequestError):
            error_msg = str(error)
            if "context" in error_msg.lower() or "token" in error_msg.lower():
                raise LLMContextLengthError(
                    f"Context length exceeded: {error}",
                    provider=provider,
                )
            raise

        # Re-raise unknown errors
        raise
