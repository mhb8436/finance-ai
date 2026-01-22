"""Ollama embedding adapter for local models.

Supports running embedding models locally via Ollama:
- nomic-embed-text
- mxbai-embed-large
- all-minilm
- snowflake-arctic-embed
- etc.
"""

import logging

import httpx

from .base import BaseEmbeddingAdapter, EmbeddingRequest, EmbeddingResponse

logger = logging.getLogger(__name__)


class OllamaEmbeddingAdapter(BaseEmbeddingAdapter):
    """Adapter for Ollama local embedding models."""

    name = "ollama"

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        api_key: str = "",  # Not needed for Ollama
        base_url: str | None = None,
        timeout: float = 120.0,
        **kwargs,
    ):
        """Initialize the Ollama adapter.

        Args:
            api_key: Not used (Ollama doesn't require auth).
            base_url: Ollama server URL (default: http://localhost:11434).
            timeout: Request timeout in seconds.
            **kwargs: Additional options.
        """
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL, timeout, **kwargs)
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client (lazy initialization)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Ollama API.

        Args:
            request: Embedding request.

        Returns:
            EmbeddingResponse with vectors.
        """
        if not request.texts:
            return EmbeddingResponse(embeddings=[], model=request.model)

        embeddings = []

        try:
            # Ollama processes one text at a time
            for text in request.texts:
                response = await self.client.post(
                    "/api/embeddings",
                    json={
                        "model": request.model,
                        "prompt": text,
                    },
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])

            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                usage={},
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def embed_batch(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Batch embedding using newer Ollama API (if available).

        Falls back to sequential if batch endpoint not available.
        """
        if not request.texts:
            return EmbeddingResponse(embeddings=[], model=request.model)

        try:
            # Try batch endpoint (Ollama 0.1.44+)
            response = await self.client.post(
                "/api/embed",
                json={
                    "model": request.model,
                    "input": request.texts,
                },
            )
            response.raise_for_status()
            data = response.json()

            return EmbeddingResponse(
                embeddings=data.get("embeddings", []),
                model=request.model,
                usage={},
            )

        except httpx.HTTPStatusError:
            # Fall back to sequential processing
            logger.debug("Batch endpoint not available, falling back to sequential")
            return await self.embed(request)

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def list_models(self) -> list[str]:
        """List available Ollama models.

        Returns:
            List of model names that support embeddings.
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model: Model name to pull.

        Returns:
            True if successful.
        """
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model},
                timeout=600.0,  # Longer timeout for downloads
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False
