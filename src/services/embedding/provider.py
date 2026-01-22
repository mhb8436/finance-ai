"""Embedding provider manager.

Manages multiple embedding adapters and provides a unified interface
for embedding generation across different providers.
"""

import logging
from typing import Type

from .adapters.base import BaseEmbeddingAdapter, EmbeddingRequest, EmbeddingResponse
from .adapters.ollama import OllamaEmbeddingAdapter
from .adapters.openai import AzureOpenAIEmbeddingAdapter, OpenAIEmbeddingAdapter
from .config import EmbeddingConfig

logger = logging.getLogger(__name__)


# Adapter registry mapping binding names to adapter classes
ADAPTER_REGISTRY: dict[str, Type[BaseEmbeddingAdapter]] = {
    "openai": OpenAIEmbeddingAdapter,
    "azure_openai": AzureOpenAIEmbeddingAdapter,
    "ollama": OllamaEmbeddingAdapter,
    # OpenAI-compatible providers use OpenAI adapter
    "deepseek": OpenAIEmbeddingAdapter,
    "groq": OpenAIEmbeddingAdapter,
    "together": OpenAIEmbeddingAdapter,
    "lm_studio": OpenAIEmbeddingAdapter,
    "vllm": OpenAIEmbeddingAdapter,
}


class EmbeddingProviderManager:
    """Manages embedding adapters for different providers.

    Supports:
    - Dynamic adapter selection based on configuration
    - Lazy adapter initialization
    - Multiple concurrent adapters
    - Custom adapter registration

    Example:
        manager = EmbeddingProviderManager()
        manager.set_adapter("openai", config)

        response = await manager.embed(request)
    """

    def __init__(self):
        """Initialize the provider manager."""
        self._adapters: dict[str, BaseEmbeddingAdapter] = {}
        self._active_binding: str | None = None

    def register_adapter(
        self,
        binding: str,
        adapter_class: Type[BaseEmbeddingAdapter],
    ) -> None:
        """Register a custom adapter class.

        Args:
            binding: Binding name (e.g., "custom_provider").
            adapter_class: Adapter class to register.
        """
        ADAPTER_REGISTRY[binding] = adapter_class
        logger.info(f"Registered embedding adapter: {binding}")

    def set_adapter(
        self,
        binding: str,
        config: EmbeddingConfig,
    ) -> BaseEmbeddingAdapter:
        """Set up and activate an adapter.

        Args:
            binding: Provider binding name.
            config: Embedding configuration.

        Returns:
            The configured adapter instance.

        Raises:
            ValueError: If binding is not supported.
        """
        if binding not in ADAPTER_REGISTRY:
            raise ValueError(
                f"Unknown embedding binding: {binding}. "
                f"Supported: {list(ADAPTER_REGISTRY.keys())}"
            )

        adapter_class = ADAPTER_REGISTRY[binding]

        # Create adapter instance with appropriate kwargs
        adapter_kwargs = {
            "api_key": config.api_key,
            "base_url": config.base_url if config.base_url else None,
            "timeout": getattr(config, "timeout", 60.0),
        }

        # Add Azure-specific settings
        if binding == "azure_openai":
            adapter_kwargs["api_version"] = getattr(config, "api_version", "2024-02-01")

        adapter = adapter_class(**adapter_kwargs)

        self._adapters[binding] = adapter
        self._active_binding = binding

        logger.info(f"Activated embedding adapter: {binding} ({adapter_class.__name__})")
        return adapter

    def get_adapter(self, binding: str | None = None) -> BaseEmbeddingAdapter:
        """Get an adapter instance.

        Args:
            binding: Specific binding to get. Uses active if None.

        Returns:
            The adapter instance.

        Raises:
            ValueError: If no adapter is available.
        """
        target = binding or self._active_binding

        if target is None:
            raise ValueError("No active embedding adapter. Call set_adapter() first.")

        if target not in self._adapters:
            raise ValueError(f"Adapter not initialized: {target}")

        return self._adapters[target]

    def get_active_adapter(self) -> BaseEmbeddingAdapter:
        """Get the currently active adapter.

        Returns:
            The active adapter instance.
        """
        return self.get_adapter()

    @property
    def active_binding(self) -> str | None:
        """Get the active binding name."""
        return self._active_binding

    async def embed(
        self,
        request: EmbeddingRequest,
        binding: str | None = None,
    ) -> EmbeddingResponse:
        """Generate embeddings using the specified or active adapter.

        Args:
            request: Embedding request.
            binding: Specific binding to use. Uses active if None.

        Returns:
            EmbeddingResponse with vectors.
        """
        adapter = self.get_adapter(binding)
        return await adapter.embed(request)

    def list_available_bindings(self) -> list[str]:
        """List all registered binding names.

        Returns:
            List of available bindings.
        """
        return list(ADAPTER_REGISTRY.keys())

    def list_active_bindings(self) -> list[str]:
        """List currently initialized bindings.

        Returns:
            List of initialized bindings.
        """
        return list(self._adapters.keys())

    async def close(self) -> None:
        """Close all adapters."""
        for binding, adapter in self._adapters.items():
            if hasattr(adapter, "close"):
                await adapter.close()
                logger.debug(f"Closed adapter: {binding}")
        self._adapters.clear()
        self._active_binding = None


# Global provider manager instance
_provider_manager: EmbeddingProviderManager | None = None


def get_provider_manager() -> EmbeddingProviderManager:
    """Get or create the global provider manager.

    Returns:
        EmbeddingProviderManager instance.
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = EmbeddingProviderManager()
    return _provider_manager


def clear_provider_manager() -> None:
    """Clear the global provider manager."""
    global _provider_manager
    _provider_manager = None
