"""OpenAI provider implementation.

Also supports OpenAI-compatible APIs (DeepSeek, Groq, etc.) and Azure OpenAI.
"""

import json
from typing import Any, AsyncIterator, Union

from openai import AsyncAzureOpenAI, AsyncOpenAI

from ..errors import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMContextLengthError,
    LLMRateLimitError,
)
from ..types import LLMConfig, LLMProvider, LLMResponse, ToolCall, ToolDefinition
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI, Azure OpenAI, and OpenAI-compatible APIs."""

    def _is_reasoning_model(self) -> bool:
        """Check if this is a reasoning model with restricted parameters.

        Reasoning models (o1, gpt-5, etc.) have restrictions:
        - Use max_completion_tokens instead of max_tokens
        - Only support temperature=1 (default)
        """
        model = self.config.model.lower()
        # Models with parameter restrictions
        reasoning_prefixes = ("o1", "gpt-5")
        return any(model.startswith(prefix) for prefix in reasoning_prefixes)

    def _use_max_completion_tokens(self) -> bool:
        """Check if this model requires max_completion_tokens instead of max_tokens."""
        if self._is_reasoning_model():
            return True
        model = self.config.model.lower()
        # Additional models that use max_completion_tokens
        new_model_prefixes = ("gpt-4o", "gpt-4-turbo")
        return any(model.startswith(prefix) for prefix in new_model_prefixes)

    @property
    def client(self) -> Union[AsyncOpenAI, AsyncAzureOpenAI]:
        """Get the OpenAI client (lazy initialization)."""
        if self._client is None:
            # Check if this is Azure OpenAI
            if self.config.provider == LLMProvider.AZURE:
                self._client = AsyncAzureOpenAI(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.base_url,
                    azure_deployment=self.config.azure_deployment or self.config.model,
                    api_version=self.config.azure_api_version,
                )
            else:
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
        return self._client

    async def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools for function calling.
            **kwargs: Additional arguments.

        Returns:
            Unified LLMResponse.
        """
        # Determine the correct parameter name for max tokens
        max_tokens_param = "max_completion_tokens" if self._use_max_completion_tokens() else "max_tokens"

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            max_tokens_param: self._get_max_tokens(max_tokens),
        }

        # Reasoning models only support temperature=1 (default), so we skip it
        if not self._is_reasoning_model():
            request_kwargs["temperature"] = self._get_temperature(temperature)

        if tools:
            request_kwargs["tools"] = [t.to_openai_format() for t in tools]

        # Add any additional kwargs
        request_kwargs.update(kwargs)

        try:
            response = await self.client.chat.completions.create(**request_kwargs)
        except Exception as e:
            self._handle_error(e)

        choice = response.choices[0]
        message = choice.message

        # Parse tool calls if present
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        # Build usage dict
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
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
        """Stream a completion using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            **kwargs: Additional arguments.

        Yields:
            Response text chunks.
        """
        # Determine the correct parameter name for max tokens
        max_tokens_param = "max_completion_tokens" if self._use_max_completion_tokens() else "max_tokens"

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            max_tokens_param: self._get_max_tokens(max_tokens),
            "stream": True,
        }

        # Reasoning models only support temperature=1 (default), so we skip it
        if not self._is_reasoning_model():
            request_kwargs["temperature"] = self._get_temperature(temperature)

        request_kwargs.update(kwargs)

        try:
            response = await self.client.chat.completions.create(**request_kwargs)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, error: Exception) -> None:
        """Convert OpenAI errors to LLM service errors."""
        from openai import (
            APIConnectionError,
            AuthenticationError,
            BadRequestError,
            RateLimitError,
        )

        provider = self.config.provider.value if self.config.provider else "openai"

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
            if "context_length" in error_msg.lower() or "token" in error_msg.lower():
                raise LLMContextLengthError(
                    f"Context length exceeded: {error}",
                    provider=provider,
                )
            raise

        # Re-raise unknown errors
        raise
