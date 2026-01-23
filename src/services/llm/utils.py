"""Utility functions for LLM service."""

from urllib.parse import urlparse

from .types import LLMProvider


# URL patterns for provider detection
PROVIDER_URL_PATTERNS: dict[str, LLMProvider] = {
    "api.openai.com": LLMProvider.OPENAI,
    "openai.azure.com": LLMProvider.AZURE,  # Azure OpenAI
    "cognitiveservices.azure.com": LLMProvider.AZURE,  # Azure Cognitive Services
    "api.anthropic.com": LLMProvider.ANTHROPIC,
    "api.deepseek.com": LLMProvider.DEEPSEEK,
    "api.groq.com": LLMProvider.GROQ,
}

# Localhost patterns indicating local providers
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}

# Default ports for local providers
LOCAL_PROVIDER_PORTS = {
    11434: "ollama",  # Ollama default
    8000: "vllm",  # vLLM default
    1234: "lmstudio",  # LM Studio default
}


def detect_provider_from_url(base_url: str) -> LLMProvider:
    """Detect LLM provider from base URL.

    Args:
        base_url: The API base URL.

    Returns:
        Detected LLMProvider.
    """
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    port = parsed.port

    # Check for known provider URLs
    for pattern, provider in PROVIDER_URL_PATTERNS.items():
        if pattern in host:
            return provider

    # Check for local providers
    if host in LOCAL_HOSTS:
        return LLMProvider.LOCAL

    # Default to OpenAI-compatible
    return LLMProvider.OPENAI


def detect_provider_from_model(model: str) -> LLMProvider | None:
    """Detect provider from model name.

    Args:
        model: Model name.

    Returns:
        Detected LLMProvider or None if not detected.
    """
    model_lower = model.lower()

    # Claude models
    if model_lower.startswith("claude"):
        return LLMProvider.ANTHROPIC

    # DeepSeek models
    if "deepseek" in model_lower:
        return LLMProvider.DEEPSEEK

    # Groq models (common ones)
    groq_models = ["llama", "mixtral", "gemma"]
    if any(m in model_lower for m in groq_models):
        # Could be Groq or local, return None to let URL decide
        return None

    # OpenAI models
    openai_prefixes = ["gpt-", "o1-", "o3-", "text-", "davinci", "curie", "babbage", "ada"]
    if any(model_lower.startswith(p) for p in openai_prefixes):
        return LLMProvider.OPENAI

    return None


def infer_provider(
    base_url: str,
    model: str,
    binding: str | None = None,
) -> LLMProvider:
    """Infer the LLM provider from configuration.

    Priority:
    1. Explicit binding if provided
    2. URL-based detection
    3. Model-based detection (as fallback hint)

    Args:
        base_url: The API base URL.
        model: Model name.
        binding: Explicit provider binding (e.g., "openai", "anthropic").

    Returns:
        Inferred LLMProvider.
    """
    # 1. Explicit binding takes priority
    if binding:
        try:
            return LLMProvider(binding.lower())
        except ValueError:
            pass  # Invalid binding, continue with detection

    # 2. URL-based detection
    url_provider = detect_provider_from_url(base_url)

    # 3. For local providers, we might want to use model hints
    if url_provider == LLMProvider.LOCAL:
        model_provider = detect_provider_from_model(model)
        # If model suggests a specific cloud provider but URL is local,
        # it's probably a local deployment, so keep LOCAL
        return LLMProvider.LOCAL

    # 4. If URL detection gives OpenAI but model suggests otherwise
    if url_provider == LLMProvider.OPENAI:
        model_provider = detect_provider_from_model(model)
        if model_provider and model_provider != LLMProvider.OPENAI:
            return model_provider

    return url_provider


def get_local_provider_type(base_url: str) -> str:
    """Detect the type of local provider.

    Args:
        base_url: The API base URL.

    Returns:
        Local provider type ("ollama", "vllm", "lmstudio", or "unknown").
    """
    parsed = urlparse(base_url)
    port = parsed.port

    if port and port in LOCAL_PROVIDER_PORTS:
        return LOCAL_PROVIDER_PORTS[port]

    return "unknown"


def normalize_base_url(base_url: str) -> str:
    """Normalize the base URL for API calls.

    Args:
        base_url: The API base URL.

    Returns:
        Normalized URL.
    """
    # Remove trailing slash
    url = base_url.rstrip("/")

    # Ensure /v1 suffix for OpenAI-compatible APIs
    # (skip for Anthropic which doesn't use /v1)
    if "anthropic.com" not in url and not url.endswith("/v1"):
        # Check if it looks like it needs /v1
        parsed = urlparse(url)
        if not parsed.path or parsed.path == "/":
            url = url + "/v1"

    return url
