"""Embedding Service Module.

Provides multi-provider embedding support for FinanceAI RAG system.

Supported Providers:
- openai: OpenAI embeddings (text-embedding-3-small, text-embedding-3-large)
- azure_openai: Azure OpenAI embeddings
- ollama: Local Ollama models (nomic-embed-text, mxbai-embed-large)
- deepseek, groq, together: OpenAI-compatible providers

Usage:
    # Default (OpenAI from environment)
    from src.services.embedding import get_embedding_client

    client = get_embedding_client()
    embeddings = await client.embed(["text1", "text2"])

    # With Ollama
    from src.services.embedding import EmbeddingClient, EmbeddingConfig

    config = EmbeddingConfig(binding="ollama", model="nomic-embed-text")
    client = EmbeddingClient(config)
    embeddings = await client.embed(["local embedding test"])

Environment Variables:
    EMBEDDING_MODEL: Model name (default: text-embedding-3-small)
    EMBEDDING_API_KEY: API key (falls back to LLM_API_KEY)
    EMBEDDING_HOST: Base URL for the API
    EMBEDDING_BINDING: Provider binding (openai, ollama, etc.)
    EMBEDDING_DIMENSION: Embedding dimensions (default: 1536)
"""

from .adapters import (
    BaseEmbeddingAdapter,
    EmbeddingRequest,
    EmbeddingResponse,
    OllamaEmbeddingAdapter,
    OpenAIEmbeddingAdapter,
)
from .client import EmbeddingClient, clear_embedding_client, get_embedding_client
from .config import EmbeddingConfig
from .provider import EmbeddingProviderManager, get_provider_manager

__all__ = [
    # Client
    "EmbeddingClient",
    "EmbeddingConfig",
    "get_embedding_client",
    "clear_embedding_client",
    # Provider
    "EmbeddingProviderManager",
    "get_provider_manager",
    # Adapters
    "BaseEmbeddingAdapter",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "OpenAIEmbeddingAdapter",
    "OllamaEmbeddingAdapter",
]
