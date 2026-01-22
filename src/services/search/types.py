"""Type definitions for web search service."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Citation:
    """A citation from search results."""

    id: int
    title: str
    url: str
    snippet: str = ""
    date: str | None = None
    source: str = ""
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "date": self.date,
            "source": self.source,
            "content": self.content,
        }


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str
    date: str | None = None
    source: str = ""
    content: str = ""
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "date": self.date,
            "source": self.source,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class WebSearchResponse:
    """Unified response from web search."""

    query: str
    answer: str
    provider: str
    citations: list[Citation] = field(default_factory=list)
    search_results: list[SearchResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "answer": self.answer,
            "provider": self.provider,
            "citations": [c.to_dict() for c in self.citations],
            "search_results": [r.to_dict() for r in self.search_results],
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
