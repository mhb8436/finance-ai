"""Semantic chunker using embeddings."""

import numpy as np
from typing import Callable, Awaitable

from ..base import BaseChunker
from ...types import Chunk, Document


class SemanticChunker(BaseChunker):
    """Semantic chunker that splits based on embedding similarity."""

    def __init__(
        self,
        embedding_func: Callable[[list[str]], Awaitable[list[list[float]]]],
        similarity_threshold: float = 0.5,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
    ):
        """Initialize the semantic chunker.

        Args:
            embedding_func: Async function to generate embeddings.
            similarity_threshold: Threshold for semantic similarity (0-1).
            min_chunk_size: Minimum chunk size in characters.
            max_chunk_size: Maximum chunk size in characters.
        """
        self.embedding_func = embedding_func
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, document: Document) -> list[Chunk]:
        """Split document into semantic chunks.

        Note: This is a sync wrapper. For full async support,
        use chunk_async instead.

        Args:
            document: Document to chunk.

        Returns:
            List of Chunk objects.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't use asyncio.run in running loop
                # Fall back to simple chunking
                return self._simple_chunk(document)
        except RuntimeError:
            pass

        return asyncio.run(self.chunk_async(document))

    async def chunk_async(self, document: Document) -> list[Chunk]:
        """Async version of chunk.

        Args:
            document: Document to chunk.

        Returns:
            List of Chunk objects.
        """
        text = document.get_all_text()
        if not text.strip():
            return []

        # Split into sentences first
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return [
                Chunk(
                    content=text,
                    chunk_type="text",
                    metadata={"source": document.file_path},
                )
            ]

        # Get embeddings for all sentences
        embeddings = await self.embedding_func(sentences)

        # Find semantic boundaries
        boundaries = self._find_boundaries(embeddings)

        # Create chunks
        chunks: list[Chunk] = []
        current_start = 0

        for boundary in boundaries:
            chunk_text = " ".join(sentences[current_start : boundary + 1])

            # Enforce size limits
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        chunk_type="text",
                        metadata={
                            "chunk_index": len(chunks),
                            "source": document.file_path,
                            "semantic": True,
                        },
                    )
                )
                current_start = boundary + 1

        # Add remaining text
        if current_start < len(sentences):
            remaining = " ".join(sentences[current_start:])
            if remaining.strip():
                chunks.append(
                    Chunk(
                        content=remaining,
                        chunk_type="text",
                        metadata={
                            "chunk_index": len(chunks),
                            "source": document.file_path,
                            "semantic": True,
                        },
                    )
                )

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        import re

        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_boundaries(self, embeddings: list[list[float]]) -> list[int]:
        """Find semantic boundaries based on embedding similarity.

        Args:
            embeddings: List of sentence embeddings.

        Returns:
            List of boundary indices.
        """
        if len(embeddings) < 2:
            return [len(embeddings) - 1]

        boundaries: list[int] = []
        current_chunk_start = 0
        current_chunk_size = 0

        for i in range(len(embeddings) - 1):
            # Calculate similarity with next sentence
            similarity = self._cosine_similarity(embeddings[i], embeddings[i + 1])

            current_chunk_size += 1  # Approximate

            # Check if we should create a boundary
            should_split = (
                similarity < self.similarity_threshold
                and current_chunk_size >= 2  # At least 2 sentences
            )

            if should_split:
                boundaries.append(i)
                current_chunk_start = i + 1
                current_chunk_size = 0

        # Add final boundary
        boundaries.append(len(embeddings) - 1)

        return boundaries

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity (0-1).
        """
        a_np = np.array(a)
        b_np = np.array(b)

        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def _simple_chunk(self, document: Document) -> list[Chunk]:
        """Simple fallback chunking.

        Args:
            document: Document to chunk.

        Returns:
            List of Chunk objects.
        """
        from .text_chunker import TextChunker

        simple_chunker = TextChunker(
            chunk_size=self.max_chunk_size,
            chunk_overlap=200,
        )
        return simple_chunker.chunk(document)
