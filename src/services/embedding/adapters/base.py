"""Base embedding adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class EmbeddingRequest:
    """Request for embedding generation."""

    texts: list[str]
    model: str
    dimensions: int | None = None
    input_type: Literal["query", "document"] | None = None


@dataclass
class EmbeddingResponse:
    """Response from embedding generation."""

    embeddings: list[list[float]]
    model: str
    usage: dict = field(default_factory=dict)


class BaseEmbeddingAdapter(ABC):
    """Base class for embedding adapters.

    Each adapter implements embedding generation for a specific provider.
    """

    name: str = "base"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        **kwargs,
    ):
        """Initialize the adapter.

        Args:
            api_key: API key for the provider.
            base_url: Base URL for the API (optional).
            timeout: Request timeout in seconds.
            **kwargs: Additional provider-specific options.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.extra_options = kwargs

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for the given texts.

        Args:
            request: Embedding request with texts and options.

        Returns:
            EmbeddingResponse with embedding vectors.
        """
        pass

    async def embed_single(self, text: str, model: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Text to embed.
            model: Model name to use.

        Returns:
            Embedding vector.
        """
        response = await self.embed(EmbeddingRequest(texts=[text], model=model))
        return response.embeddings[0] if response.embeddings else []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
