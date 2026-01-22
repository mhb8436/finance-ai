"""Unified embedding client with multi-provider support.

Supports multiple embedding providers:
- OpenAI (text-embedding-3-small, text-embedding-3-large)
- Azure OpenAI
- Ollama (local models: nomic-embed-text, mxbai-embed-large)
- DeepSeek, Groq, Together (OpenAI-compatible)

Usage:
    # Default (uses environment config)
    client = get_embedding_client()
    embeddings = await client.embed(["text1", "text2"])

    # With specific config
    config = EmbeddingConfig(binding="ollama", model="nomic-embed-text")
    client = EmbeddingClient(config)
    embeddings = await client.embed(["text"])
"""

import asyncio
import logging
from typing import Any, Literal

from .adapters.base import EmbeddingRequest, EmbeddingResponse
from .config import EmbeddingConfig
from .provider import EmbeddingProviderManager, get_provider_manager

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Unified embedding client supporting multiple providers.

    This client provides a consistent interface for generating embeddings
    across different providers (OpenAI, Ollama, etc.).

    Attributes:
        config: Embedding configuration.
        manager: Provider manager for handling adapters.
    """

    def __init__(self, config: EmbeddingConfig | None = None):
        """Initialize the embedding client.

        Args:
            config: Embedding configuration. Uses environment if None.
        """
        self.config = config or EmbeddingConfig.from_env()
        self._manager: EmbeddingProviderManager | None = None
        self._initialized = False

    @property
    def manager(self) -> EmbeddingProviderManager:
        """Get the provider manager (lazy initialization)."""
        if self._manager is None:
            self._manager = get_provider_manager()
        return self._manager

    def _ensure_initialized(self) -> None:
        """Ensure the adapter is initialized."""
        if not self._initialized:
            self.manager.set_adapter(self.config.binding, self.config)
            self._initialized = True

    async def embed(
        self,
        texts: list[str],
        input_type: Literal["query", "document"] | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed.
            input_type: Optional hint for embedding type (query vs document).

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        self._ensure_initialized()

        # Process in batches
        all_embeddings: list[list[float]] = []
        batch_size = self.config.batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            request = EmbeddingRequest(
                texts=batch,
                model=self.config.model,
                dimensions=self.config.dimensions,
                input_type=input_type,
            )
            response = await self.manager.embed(request)
            all_embeddings.extend(response.embeddings)

        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query text.

        Optimized for search queries (shorter, question-like).

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector.
        """
        embeddings = await self.embed([text], input_type="query")
        return embeddings[0] if embeddings else []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document texts.

        Optimized for document chunks (longer, content-like).

        Args:
            texts: Document texts to embed.

        Returns:
            List of embedding vectors.
        """
        return await self.embed(texts, input_type="document")

    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding (for compatibility).

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.embed(texts))
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self.embed(texts))

    def get_embedding_func(self) -> Any:
        """Get embedding function for LightRAG compatibility.

        Returns a callable that can be used with LightRAG's
        embedding_func parameter.

        Returns:
            Async callable for embedding generation.
        """

        async def embedding_func(texts: list[str]) -> list[list[float]]:
            return await self.embed(texts)

        return embedding_func

    def get_embedding_func_numpy(self) -> Any:
        """Get embedding function returning numpy arrays.

        Useful for libraries that expect numpy arrays.

        Returns:
            Async callable returning numpy arrays.
        """
        import numpy as np

        async def embedding_func(texts: list[str]) -> Any:
            embeddings = await self.embed(texts)
            return np.array(embeddings)

        return embedding_func

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions."""
        return self.config.dimensions

    @property
    def model(self) -> str:
        """Get the model name."""
        return self.config.model

    @property
    def binding(self) -> str:
        """Get the binding name."""
        return self.config.binding

    async def close(self) -> None:
        """Close the client and release resources."""
        if self._manager:
            await self._manager.close()
            self._initialized = False


# Singleton instance
_embedding_client: EmbeddingClient | None = None


def get_embedding_client(config: EmbeddingConfig | None = None) -> EmbeddingClient:
    """Get or create the embedding client singleton.

    Args:
        config: Optional config to override default.

    Returns:
        EmbeddingClient instance.
    """
    global _embedding_client

    if _embedding_client is None or config is not None:
        _embedding_client = EmbeddingClient(config)

    return _embedding_client


def clear_embedding_client() -> None:
    """Clear the cached embedding client."""
    global _embedding_client
    _embedding_client = None
