"""LLM Service Factory - main entry point for LLM operations."""

from typing import Any, AsyncIterator

from src.core.config import get_llm_config

from .providers.anthropic_provider import AnthropicProvider
from .providers.base import BaseProvider
from .providers.local_provider import LocalProvider
from .providers.openai_provider import OpenAIProvider
from .types import LLMConfig, LLMProvider, LLMResponse, ToolDefinition, parse_openai_tool_definitions
from .utils import infer_provider

# Provider registry
_provider_registry: dict[LLMProvider, type[BaseProvider]] = {
    LLMProvider.OPENAI: OpenAIProvider,
    LLMProvider.AZURE: OpenAIProvider,  # Azure OpenAI uses OpenAIProvider with different client
    LLMProvider.ANTHROPIC: AnthropicProvider,
    LLMProvider.DEEPSEEK: OpenAIProvider,  # DeepSeek uses OpenAI-compatible API
    LLMProvider.GROQ: OpenAIProvider,  # Groq uses OpenAI-compatible API
    LLMProvider.LOCAL: LocalProvider,
}

# Cached provider instance
_cached_provider: BaseProvider | None = None
_cached_config_hash: str | None = None


def _get_config_hash(config: LLMConfig) -> str:
    """Generate a hash for config comparison."""
    return f"{config.model}:{config.api_key}:{config.base_url}:{config.provider}"


def get_provider(config: LLMConfig | None = None) -> BaseProvider:
    """Get or create an LLM provider instance.

    Args:
        config: LLM configuration. If None, uses environment config.

    Returns:
        Configured LLM provider instance.
    """
    global _cached_provider, _cached_config_hash

    if config is None:
        # Load config from environment
        llm_config = get_llm_config()
        config = LLMConfig(
            model=llm_config["model"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            provider=None,  # Will be auto-detected
            # Azure-specific settings
            azure_deployment=llm_config.get("azure_deployment"),
            azure_api_version=llm_config.get("azure_api_version", "2024-02-01"),
        )

    # Infer provider if not set
    if config.provider is None:
        llm_config = get_llm_config()
        binding = llm_config.get("binding")
        config.provider = infer_provider(config.base_url, config.model, binding)

    # Check if we can reuse cached provider
    config_hash = _get_config_hash(config)
    if _cached_provider is not None and _cached_config_hash == config_hash:
        return _cached_provider

    # Create new provider
    provider_class = _provider_registry.get(config.provider, OpenAIProvider)
    _cached_provider = provider_class(config)
    _cached_config_hash = config_hash

    return _cached_provider


async def complete(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    tools: list[dict[str, Any]] | list[ToolDefinition] | None = None,
    config: LLMConfig | None = None,
    **kwargs: Any,
) -> LLMResponse:
    """Generate a completion using the configured LLM provider.

    This is the main entry point for non-streaming completions.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        model: Override model for this call.
        temperature: Override temperature for this call.
        max_tokens: Override max_tokens for this call.
        tools: Optional list of tools (OpenAI format or ToolDefinition objects).
        config: Custom LLM config. If None, uses environment config.
        **kwargs: Additional provider-specific arguments.

    Returns:
        Unified LLMResponse.
    """
    provider = get_provider(config)

    # Override model if provided
    if model:
        provider.config.model = model

    # Convert OpenAI-format tools to ToolDefinition if needed
    tool_definitions: list[ToolDefinition] | None = None
    if tools:
        if tools and isinstance(tools[0], dict):
            tool_definitions = parse_openai_tool_definitions(tools)
        else:
            tool_definitions = tools

    return await provider.complete(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tool_definitions,
        **kwargs,
    )


async def stream(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    config: LLMConfig | None = None,
    **kwargs: Any,
) -> AsyncIterator[str]:
    """Stream a completion using the configured LLM provider.

    This is the main entry point for streaming completions.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        model: Override model for this call.
        temperature: Override temperature for this call.
        max_tokens: Override max_tokens for this call.
        config: Custom LLM config. If None, uses environment config.
        **kwargs: Additional provider-specific arguments.

    Yields:
        Response text chunks.
    """
    provider = get_provider(config)

    # Override model if provided
    if model:
        provider.config.model = model

    async for chunk in provider.stream(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    ):
        yield chunk


def clear_cache() -> None:
    """Clear the cached provider instance.

    Call this when configuration changes to force re-creation.
    """
    global _cached_provider, _cached_config_hash
    _cached_provider = None
    _cached_config_hash = None
