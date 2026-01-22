"""Simple text chunker with overlap."""

import re

from ..base import BaseChunker
from ...types import Chunk, Document


class TextChunker(BaseChunker):
    """Simple text chunker with configurable size and overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ):
        """Initialize the chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Overlap between consecutive chunks.
            separators: List of separators to split on, in order of priority.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, document: Document) -> list[Chunk]:
        """Split document into chunks.

        Args:
            document: Document to chunk.

        Returns:
            List of Chunk objects.
        """
        # If document already has chunks (e.g., from PDF parser), use those
        if document.chunks:
            return self._rechunk_existing(document.chunks)

        # Otherwise, chunk the main content
        text = document.content
        if not text.strip():
            return []

        chunks = self._split_text(text)

        return [
            Chunk(
                content=chunk_text,
                chunk_type="text",
                metadata={
                    "chunk_index": i,
                    "source": document.file_path,
                },
            )
            for i, chunk_text in enumerate(chunks)
        ]

    def _rechunk_existing(self, chunks: list[Chunk]) -> list[Chunk]:
        """Re-chunk existing chunks if they are too large.

        Args:
            chunks: Existing chunks from document.

        Returns:
            List of properly sized chunks.
        """
        result: list[Chunk] = []

        for chunk in chunks:
            if len(chunk.content) <= self.chunk_size:
                result.append(chunk)
            else:
                # Split large chunk
                sub_chunks = self._split_text(chunk.content)
                for i, sub_text in enumerate(sub_chunks):
                    new_chunk = Chunk(
                        content=sub_text,
                        chunk_type=chunk.chunk_type,
                        metadata={
                            **chunk.metadata,
                            "sub_chunk_index": i,
                        },
                    )
                    result.append(new_chunk)

        return result

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks using separators.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        chunks: list[str] = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = re.split(r"\n\s*\n", text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + para
                else:
                    # Paragraph itself is too large, split it
                    para_chunks = self._split_large_text(para)
                    chunks.extend(para_chunks[:-1])
                    current_chunk = para_chunks[-1] if para_chunks else ""
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_text(self, text: str) -> list[str]:
        """Split text that's larger than chunk_size.

        Args:
            text: Large text to split.

        Returns:
            List of smaller text chunks.
        """
        chunks: list[str] = []

        # Try splitting by sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                    overlap_text = self._get_overlap(current)
                    current = overlap_text + sentence
                else:
                    # Single sentence too large, split by words
                    if len(sentence) > self.chunk_size:
                        word_chunks = self._split_by_words(sentence)
                        chunks.extend(word_chunks[:-1])
                        current = word_chunks[-1] if word_chunks else ""
                    else:
                        current = sentence
            else:
                if current:
                    current += " " + sentence
                else:
                    current = sentence

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _split_by_words(self, text: str) -> list[str]:
        """Split text by words when sentences are too large.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        words = text.split()
        chunks: list[str] = []
        current = ""

        for word in words:
            if len(current) + len(word) + 1 > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                    current = word
                else:
                    # Single word too large (unlikely), just add it
                    chunks.append(word)
            else:
                if current:
                    current += " " + word
                else:
                    current = word

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk.

        Args:
            text: Text to get overlap from.

        Returns:
            Overlap text.
        """
        if len(text) <= self.chunk_overlap:
            return text + " "

        # Try to break at sentence boundary
        overlap_text = text[-self.chunk_overlap :]
        sentence_break = overlap_text.find(". ")
        if sentence_break > 0:
            return overlap_text[sentence_break + 2 :]

        # Try word boundary
        word_break = overlap_text.find(" ")
        if word_break > 0:
            return overlap_text[word_break + 1 :]

        return overlap_text
