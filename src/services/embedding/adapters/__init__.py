"""Embedding adapters for different providers."""

from .base import BaseEmbeddingAdapter, EmbeddingRequest, EmbeddingResponse
from .openai import OpenAIEmbeddingAdapter
from .ollama import OllamaEmbeddingAdapter

__all__ = [
    "BaseEmbeddingAdapter",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "OpenAIEmbeddingAdapter",
    "OllamaEmbeddingAdapter",
]
