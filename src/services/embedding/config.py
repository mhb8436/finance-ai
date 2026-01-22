"""Embedding configuration."""

import os
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""

    model: str = "text-embedding-3-small"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    binding: str = "openai"  # openai, azure_openai, ollama
    dimensions: int = 1536
    max_tokens: int = 8192
    batch_size: int = 100
    api_version: str = "2024-02-01"  # For Azure OpenAI
    deployment: str = ""  # Azure deployment name (overrides model for Azure)

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create config from environment variables."""
        # Determine binding - support 'azure' as alias for 'azure_openai'
        binding = os.getenv("EMBEDDING_BINDING", "openai")
        if binding == "azure":
            binding = "azure_openai"

        # For Azure, use EMBEDDING_DEPLOYMENT if set, otherwise fall back to EMBEDDING_MODEL
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        deployment = os.getenv("EMBEDDING_DEPLOYMENT", "")

        # If using Azure and deployment is set, use deployment as model name
        if binding == "azure_openai" and deployment:
            model = deployment

        return cls(
            model=model,
            api_key=os.getenv("EMBEDDING_API_KEY", os.getenv("LLM_API_KEY", "")),
            base_url=os.getenv("EMBEDDING_HOST", "https://api.openai.com/v1"),
            binding=binding,
            dimensions=int(os.getenv("EMBEDDING_DIMENSION", "1536")),
            api_version=os.getenv("AZURE_API_VERSION", "2024-02-01"),
            deployment=deployment,
        )
