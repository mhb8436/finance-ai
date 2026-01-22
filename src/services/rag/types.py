"""Type definitions for RAG service."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A chunk of text from a document."""

    content: str
    chunk_type: str = "text"  # text, table, financial, news
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Document:
    """A parsed document."""

    content: str
    file_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.chunks is None:
            self.chunks = []

    def add_chunk(self, chunk: Chunk) -> None:
        """Add a chunk to the document."""
        self.chunks.append(chunk)

    def get_all_text(self) -> str:
        """Get all text from chunks."""
        if self.chunks:
            return "\n\n".join(c.content for c in self.chunks)
        return self.content


@dataclass
class SearchResult:
    """Result from RAG search."""

    query: str
    answer: str
    content: str  # Retrieved context
    mode: str = "hybrid"
    provider: str = "default"
    chunks: list[Chunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "answer": self.answer,
            "content": self.content,
            "mode": self.mode,
            "provider": self.provider,
            "chunks": [
                {"content": c.content, "type": c.chunk_type, "metadata": c.metadata}
                for c in self.chunks
            ],
            "metadata": self.metadata,
        }
