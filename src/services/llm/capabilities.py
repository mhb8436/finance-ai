"""Provider and model capabilities definitions."""

from dataclasses import dataclass

from .types import LLMProvider


@dataclass
class ModelCapabilities:
    """Capabilities of a specific model."""

    supports_tools: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_json_mode: bool = False
    max_context_tokens: int = 128000
    max_output_tokens: int = 4096


# Default capabilities by provider
PROVIDER_DEFAULTS: dict[LLMProvider, ModelCapabilities] = {
    LLMProvider.OPENAI: ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=16384,
    ),
    LLMProvider.ANTHROPIC: ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200000,
        max_output_tokens=8192,
    ),
    LLMProvider.DEEPSEEK: ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=64000,
        max_output_tokens=8192,
    ),
    LLMProvider.GROQ: ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=32768,
        max_output_tokens=8192,
    ),
    LLMProvider.LOCAL: ModelCapabilities(
        supports_tools=False,  # Depends on model
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=False,
        max_context_tokens=32768,
        max_output_tokens=4096,
    ),
}

# Model-specific capability overrides
MODEL_CAPABILITIES: dict[str, ModelCapabilities] = {
    # OpenAI models
    "gpt-4o": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=16384,
    ),
    "gpt-4-turbo": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=4096,
    ),
    "o1": ModelCapabilities(
        supports_tools=False,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200000,
        max_output_tokens=100000,
    ),
    "o1-mini": ModelCapabilities(
        supports_tools=False,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=False,
        max_context_tokens=128000,
        max_output_tokens=65536,
    ),
    # Anthropic models
    "claude-3-5-sonnet-20241022": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200000,
        max_output_tokens=8192,
    ),
    "claude-3-5-haiku-20241022": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200000,
        max_output_tokens=8192,
    ),
    "claude-3-opus-20240229": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200000,
        max_output_tokens=4096,
    ),
    # DeepSeek models
    "deepseek-chat": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=64000,
        max_output_tokens=8192,
    ),
    "deepseek-coder": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=64000,
        max_output_tokens=8192,
    ),
    # Groq models
    "llama-3.3-70b-versatile": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=32768,
    ),
    "llama-3.1-8b-instant": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=128000,
        max_output_tokens=8192,
    ),
    "mixtral-8x7b-32768": ModelCapabilities(
        supports_tools=True,
        supports_streaming=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=32768,
        max_output_tokens=8192,
    ),
}


def get_model_capabilities(
    model: str,
    provider: LLMProvider,
) -> ModelCapabilities:
    """Get capabilities for a specific model.

    Args:
        model: Model name.
        provider: LLM provider.

    Returns:
        ModelCapabilities for the model.
    """
    # Check for exact model match
    if model in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model]

    # Check for partial model match (for versioned models)
    for model_name, caps in MODEL_CAPABILITIES.items():
        if model.startswith(model_name) or model_name.startswith(model):
            return caps

    # Fall back to provider defaults
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS[LLMProvider.OPENAI])
