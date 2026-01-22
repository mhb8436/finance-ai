"""Local provider implementation for Ollama, vLLM, LM Studio, etc."""

from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from ..errors import LLMConnectionError
from ..types import LLMConfig, LLMResponse, ToolCall, ToolDefinition
from ..utils import get_local_provider_type
from .base import BaseProvider


# Tool calling prompt template for models that don't support native tools
TOOL_PROMPT_TEMPLATE = """You have access to the following tools:

{tool_descriptions}

When you need to use a tool, respond with a JSON object in the following format:
```json
{{"tool": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}
```

If you don't need to use a tool, just respond normally without any JSON.
"""


class LocalProvider(BaseProvider):
    """Provider for local LLM servers (Ollama, vLLM, LM Studio).

    Uses OpenAI-compatible API format.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._local_type = get_local_provider_type(config.base_url)

    @property
    def client(self) -> AsyncOpenAI:
        """Get the OpenAI-compatible client (lazy initialization)."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key or "local",  # Local servers often don't need API key
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
        """Generate a completion using local LLM server.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            tools: Optional list of tools (injected into prompt if server doesn't support native tools).
            **kwargs: Additional arguments.

        Returns:
            Unified LLMResponse.
        """
        # If tools are provided, try native tool calling first
        # Fall back to prompt injection if it fails
        processed_messages = messages.copy()

        if tools:
            processed_messages = self._inject_tools_into_prompt(messages, tools)

        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": processed_messages,
            "temperature": self._get_temperature(temperature),
            "max_tokens": self._get_max_tokens(max_tokens),
        }

        request_kwargs.update(kwargs)

        try:
            response = await self.client.chat.completions.create(**request_kwargs)
        except Exception as e:
            self._handle_error(e)

        choice = response.choices[0]
        message = choice.message
        content = message.content or ""

        # Try to parse tool calls from response if tools were provided
        tool_calls = []
        if tools:
            parsed_content, tool_calls = self._parse_tool_response(content)
            content = parsed_content

        # Build usage dict
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
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
        """Stream a completion using local LLM server.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Override temperature for this call.
            max_tokens: Override max_tokens for this call.
            **kwargs: Additional arguments.

        Yields:
            Response text chunks.
        """
        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self._get_temperature(temperature),
            "max_tokens": self._get_max_tokens(max_tokens),
            "stream": True,
        }

        request_kwargs.update(kwargs)

        try:
            response = await self.client.chat.completions.create(**request_kwargs)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self._handle_error(e)

    def _inject_tools_into_prompt(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolDefinition],
    ) -> list[dict[str, Any]]:
        """Inject tool descriptions into the system prompt.

        Args:
            messages: Original messages.
            tools: Tool definitions.

        Returns:
            Messages with tools injected into system prompt.
        """
        # Build tool descriptions
        tool_descriptions = []
        for tool in tools:
            params_str = ", ".join(
                f"{p.name}: {p.type}" + (" (required)" if p.required else " (optional)")
                for p in tool.parameters
            )
            tool_descriptions.append(
                f"- {tool.name}({params_str}): {tool.description}"
            )

        tool_prompt = TOOL_PROMPT_TEMPLATE.format(
            tool_descriptions="\n".join(tool_descriptions)
        )

        # Find or create system message
        result = []
        system_found = False

        for msg in messages:
            if msg["role"] == "system":
                result.append({
                    "role": "system",
                    "content": msg["content"] + "\n\n" + tool_prompt,
                })
                system_found = True
            else:
                result.append(msg)

        if not system_found:
            result.insert(0, {"role": "system", "content": tool_prompt})

        return result

    def _parse_tool_response(
        self,
        content: str,
    ) -> tuple[str, list[ToolCall]]:
        """Parse tool calls from model response.

        Args:
            content: Model response content.

        Returns:
            Tuple of (cleaned content, list of tool calls).
        """
        import json
        import re

        tool_calls = []

        # Look for JSON blocks in the response
        json_pattern = r"```json\s*(\{.*?\})\s*```"
        matches = re.findall(json_pattern, content, re.DOTALL)

        for i, match in enumerate(matches):
            try:
                data = json.loads(match)
                if "tool" in data and "arguments" in data:
                    tool_calls.append(
                        ToolCall(
                            id=f"local_{i}",
                            name=data["tool"],
                            arguments=data["arguments"],
                        )
                    )
            except json.JSONDecodeError:
                continue

        # Remove JSON blocks from content
        cleaned_content = re.sub(json_pattern, "", content).strip()

        return cleaned_content, tool_calls

    def _handle_error(self, error: Exception) -> None:
        """Convert local provider errors to LLM service errors."""
        from openai import APIConnectionError

        provider = f"local ({self._local_type})"

        if isinstance(error, APIConnectionError):
            raise LLMConnectionError(
                f"Failed to connect to local LLM server at {self.config.base_url}: {error}",
                provider=provider,
            )

        # Re-raise unknown errors
        raise
