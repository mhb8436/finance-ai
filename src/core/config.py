"""Configuration management for FinanceAI."""

import os
from pathlib import Path
from typing import Any

import yaml

_config_cache: dict[str, Any] = {}


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def load_yaml_config(config_name: str) -> dict[str, Any]:
    """Load a YAML configuration file."""
    if config_name in _config_cache:
        return _config_cache[config_name]

    config_path = get_project_root() / "config" / config_name
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    _config_cache[config_name] = config
    return config


def get_config() -> dict[str, Any]:
    """Get the main configuration."""
    return load_yaml_config("main.yaml")


def get_llm_config() -> dict[str, Any]:
    """Get LLM configuration from environment variables.

    Supported providers (auto-detected from LLM_HOST or set via LLM_BINDING):
    - openai: OpenAI API (default)
    - azure: Azure OpenAI API
    - anthropic: Anthropic Claude API
    - deepseek: DeepSeek API
    - groq: Groq API
    - local: Local servers (Ollama, vLLM, LM Studio)

    For Azure OpenAI, set:
    - LLM_BINDING=azure
    - LLM_HOST=https://{resource-name}.openai.azure.com/
    - LLM_API_KEY=your-azure-api-key
    - AZURE_DEPLOYMENT=your-deployment-name (optional, defaults to LLM_MODEL)
    - AZURE_API_VERSION=2024-02-01 (optional)
    """
    return {
        "model": os.getenv("LLM_MODEL", "gpt-4o"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_HOST", "https://api.openai.com/v1"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
        "binding": os.getenv("LLM_BINDING"),  # Optional: openai, azure, anthropic, deepseek, groq, local
        # Azure-specific settings
        "azure_deployment": os.getenv("AZURE_DEPLOYMENT"),
        "azure_api_version": os.getenv("AZURE_API_VERSION", "2024-02-01"),
    }


def get_embedding_config() -> dict[str, Any]:
    """Get embedding configuration from environment variables."""
    return {
        "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        "api_key": os.getenv("EMBEDDING_API_KEY", os.getenv("LLM_API_KEY", "")),
        "base_url": os.getenv("EMBEDDING_HOST", "https://api.openai.com/v1"),
        "dimension": int(os.getenv("EMBEDDING_DIMENSION", "1536")),
    }


def get_data_provider_config() -> dict[str, Any]:
    """Get data provider configuration."""
    return {
        "alpha_vantage_key": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
        "opendart_key": os.getenv("OPENDART_API_KEY", ""),
        "default_provider": os.getenv("DEFAULT_DATA_PROVIDER", "yfinance"),
    }
