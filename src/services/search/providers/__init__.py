"""Search providers module with registry pattern."""

from typing import Type

from ..base import BaseSearchProvider

# Provider registry
_PROVIDERS: dict[str, Type[BaseSearchProvider]] = {}


def register_provider(name: str):
    """Decorator to register a search provider.

    Args:
        name: Provider name for registration.

    Returns:
        Decorator function.
    """

    def decorator(cls: Type[BaseSearchProvider]) -> Type[BaseSearchProvider]:
        _PROVIDERS[name] = cls
        return cls

    return decorator


def get_provider(name: str, api_key: str | None = None) -> BaseSearchProvider:
    """Get a provider instance by name.

    Args:
        name: Provider name.
        api_key: Optional API key override.

    Returns:
        Provider instance.

    Raises:
        ValueError: If provider not found.
    """
    if name not in _PROVIDERS:
        available = list(_PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {name}. Available: {available}")

    return _PROVIDERS[name](api_key=api_key)


def list_providers() -> list[str]:
    """List all registered provider names.

    Returns:
        List of provider names.
    """
    return list(_PROVIDERS.keys())


def get_available_providers(api_key: str | None = None) -> list[str]:
    """List providers that are available (have API keys).

    Args:
        api_key: Optional API key to check with.

    Returns:
        List of available provider names.
    """
    available = []
    for name, cls in _PROVIDERS.items():
        provider = cls(api_key=api_key)
        if provider.is_available():
            available.append(name)
    return available


# Auto-import providers to trigger registration
from . import serper  # noqa: F401, E402
from . import tavily  # noqa: F401, E402

__all__ = [
    "register_provider",
    "get_provider",
    "list_providers",
    "get_available_providers",
]
