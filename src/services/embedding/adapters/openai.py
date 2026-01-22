"""OpenAI-compatible embedding adapter.

Supports:
- OpenAI (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
- Azure OpenAI
- DeepSeek
- Groq
- Any OpenAI-compatible API
"""

import logging

from openai import AsyncOpenAI

from .base import BaseEmbeddingAdapter, EmbeddingRequest, EmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """Adapter for OpenAI-compatible embedding APIs."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        **kwargs,
    ):
        """Initialize the OpenAI adapter.

        Args:
            api_key: OpenAI API key.
            base_url: Base URL for the API (default: OpenAI).
            timeout: Request timeout in seconds.
            **kwargs: Additional options.
        """
        super().__init__(api_key, base_url, timeout, **kwargs)
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        """Get the OpenAI client (lazy initialization)."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using OpenAI API.

        Args:
            request: Embedding request.

        Returns:
            EmbeddingResponse with vectors.
        """
        if not request.texts:
            return EmbeddingResponse(embeddings=[], model=request.model)

        try:
            # Build kwargs for the API call
            kwargs: dict = {
                "model": request.model,
                "input": request.texts,
            }

            # Add dimensions if supported (text-embedding-3-*)
            if request.dimensions and "text-embedding-3" in request.model:
                kwargs["dimensions"] = request.dimensions

            response = await self.client.embeddings.create(**kwargs)

            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings = [item.embedding for item in sorted_data]

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise


class AzureOpenAIEmbeddingAdapter(OpenAIEmbeddingAdapter):
    """Adapter for Azure OpenAI embedding API."""

    name = "azure_openai"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        api_version: str = "2024-02-01",
        timeout: float = 60.0,
        **kwargs,
    ):
        """Initialize Azure OpenAI adapter.

        Args:
            api_key: Azure API key.
            base_url: Azure OpenAI endpoint URL.
            api_version: API version to use.
            timeout: Request timeout.
            **kwargs: Additional options.
        """
        super().__init__(api_key, base_url, timeout, **kwargs)
        self.api_version = api_version

    @property
    def client(self) -> AsyncOpenAI:
        """Get the Azure OpenAI client."""
        if self._client is None:
            from openai import AsyncAzureOpenAI

            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.base_url,
                api_version=self.api_version,
                timeout=self.timeout,
            )
        return self._client
