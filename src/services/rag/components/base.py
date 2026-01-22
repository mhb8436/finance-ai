"""Base classes for RAG components."""

from abc import ABC, abstractmethod
from typing import Any

from ..types import Chunk, Document


class BaseParser(ABC):
    """Base class for document parsers."""

    @abstractmethod
    async def parse(self, file_path: str) -> Document:
        """Parse a file into a Document.

        Args:
            file_path: Path to the file to parse.

        Returns:
            Parsed Document object.
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """Check if this parser supports the given file type.

        Args:
            file_path: Path to check.

        Returns:
            True if this parser can handle the file.
        """
        pass


class BaseChunker(ABC):
    """Base class for text chunkers."""

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """Split a document into chunks.

        Args:
            document: Document to chunk.

        Returns:
            List of Chunk objects.
        """
        pass


class BaseRetriever(ABC):
    """Base class for retrievers."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Retrieve relevant chunks for a query.

        Args:
            query: Search query.
            top_k: Number of results to return.
            **kwargs: Additional retrieval parameters.

        Returns:
            List of relevant Chunk objects.
        """
        pass

    @abstractmethod
    async def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the retriever index.

        Args:
            chunks: Chunks to index.
        """
        pass
