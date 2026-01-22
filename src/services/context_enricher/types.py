"""Context Enricher Types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.services.intent_analyzer import QueryIntent
from src.services.tool_router import ToolResult


@dataclass
class EnrichmentConfig:
    """Configuration for context enrichment."""
    max_symbols: int = 3  # Maximum symbols to process
    max_parallel_calls: int = 5  # Maximum parallel tool calls
    include_news_for_stock: bool = True  # Include news for stock queries
    news_limit: int = 5  # Number of news articles to fetch


@dataclass
class EnrichedContext:
    """Result of context enrichment."""
    intent: QueryIntent
    tool_results: list[ToolResult] = field(default_factory=list)
    context_string: str = ""  # Formatted context for LLM
    sources: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def is_enriched(self) -> bool:
        """Check if context has enrichment data."""
        return bool(self.tool_results)

    @property
    def successful_results(self) -> list[ToolResult]:
        """Get only successful tool results."""
        return [r for r in self.tool_results if r.is_success]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent": self.intent.to_dict(),
            "tool_results": [r.to_dict() for r in self.tool_results],
            "context_string_length": len(self.context_string),
            "sources": self.sources,
            "timestamp": self.timestamp,
        }
