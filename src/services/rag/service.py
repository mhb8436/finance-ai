"""RAG Service - Main entry point for RAG functionality.

Provides document indexing, retrieval, and answer generation with:
- Multi-provider embedding support
- Knowledge base persistence with metadata
- Configurable chunking strategies
- Vector-based retrieval (hybrid coming soon)
"""

import logging
import os
from pathlib import Path
from typing import Any

from ..embedding import EmbeddingConfig, get_embedding_client
from ..llm import complete
from .components.base import BaseChunker, BaseParser
from .components.chunkers import SemanticChunker, TextChunker
from .components.parsers import PDFParser, TextParser
from .components.retrievers import VectorRetriever
from .metadata import (
    ChunkConfig,
    EmbeddingInfo,
    KBMetadata,
    delete_metadata,
    discover_knowledge_bases,
    load_metadata,
    save_metadata,
)
from .types import Chunk, Document, SearchResult

logger = logging.getLogger(__name__)


class RAGService:
    """RAG Service for document indexing and retrieval.

    Features:
    - Multi-document indexing with automatic parsing
    - Configurable chunking (text, semantic)
    - Vector-based retrieval with ChromaDB
    - Optional LLM answer generation
    - Knowledge base persistence with metadata

    Example:
        service = RAGService()

        # Initialize KB with documents
        await service.initialize("my_kb", ["/path/to/doc.pdf"])

        # Search
        result = await service.search("What is the revenue?", "my_kb")
        print(result.answer)
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        embedding_config: EmbeddingConfig | None = None,
        default_chunk_strategy: str = "text",
    ):
        """Initialize the RAG service.

        Args:
            persist_directory: Directory to persist vector store data.
            embedding_config: Embedding configuration.
            default_chunk_strategy: Default chunking strategy ("text" or "semantic").
        """
        self.persist_directory = persist_directory or os.getenv(
            "RAG_PERSIST_DIR", "./data/rag"
        )
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self.embedding_config = embedding_config
        self.embedding_client = get_embedding_client(embedding_config)
        self.default_chunk_strategy = default_chunk_strategy

        # Initialize parsers
        self._parsers: list[BaseParser] = [
            PDFParser(),
            TextParser(),
        ]

        # Chunker registry
        self._chunkers: dict[str, BaseChunker] = {
            "text": TextChunker(chunk_size=1000, chunk_overlap=200),
            "semantic": SemanticChunker(
                embedding_func=self.embedding_client.embed,
                min_chunk_size=100,
                max_chunk_size=2000,
            ),
        }

        # Knowledge bases (kb_name -> retriever)
        self._knowledge_bases: dict[str, VectorRetriever] = {}
        self._kb_metadata: dict[str, KBMetadata] = {}

        # Discover existing knowledge bases
        self._discover_existing_kbs()

    def _discover_existing_kbs(self) -> None:
        """Discover and load existing knowledge bases from disk."""
        existing_kbs = discover_knowledge_bases(self.persist_directory)

        for metadata in existing_kbs:
            logger.info(f"Discovered KB: {metadata.name} ({metadata.total_chunks} chunks)")
            self._kb_metadata[metadata.name] = metadata

    def _get_chunker(self, strategy: str | None = None) -> BaseChunker:
        """Get a chunker by strategy name.

        Args:
            strategy: Chunking strategy name.

        Returns:
            BaseChunker instance.
        """
        strategy = strategy or self.default_chunk_strategy
        if strategy not in self._chunkers:
            logger.warning(f"Unknown chunk strategy: {strategy}, using 'text'")
            strategy = "text"
        return self._chunkers[strategy]

    async def create_knowledge_base(
        self,
        kb_name: str,
        chunk_strategy: str = "text",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        retrieval_mode: str = "vector",
    ) -> KBMetadata:
        """Create a new knowledge base.

        Args:
            kb_name: Name of the knowledge base.
            chunk_strategy: Chunking strategy ("text" or "semantic").
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks.
            retrieval_mode: Retrieval mode ("vector" or "hybrid").

        Returns:
            KBMetadata for the created KB.
        """
        if kb_name in self._kb_metadata:
            logger.info(f"KB already exists: {kb_name}")
            return self._kb_metadata[kb_name]

        # Create metadata
        metadata = KBMetadata(
            name=kb_name,
            provider="chromadb",
            retrieval_mode=retrieval_mode,
            chunk_config=ChunkConfig(
                strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ),
            embedding_info=EmbeddingInfo(
                model=self.embedding_client.model,
                binding=self.embedding_client.binding,
                dimensions=self.embedding_client.dimensions,
            ),
        )

        # Create KB directory
        kb_dir = os.path.join(self.persist_directory, kb_name)
        Path(kb_dir).mkdir(parents=True, exist_ok=True)

        # Save metadata
        save_metadata(metadata, kb_dir)
        self._kb_metadata[kb_name] = metadata

        # Create retriever
        self._get_or_create_retriever(kb_name)

        logger.info(f"Created KB: {kb_name}")
        return metadata

    async def initialize(
        self,
        kb_name: str,
        file_paths: list[str],
        chunk_strategy: str | None = None,
    ) -> dict[str, Any]:
        """Initialize a knowledge base with documents.

        Creates the KB if it doesn't exist, then indexes the documents.

        Args:
            kb_name: Name of the knowledge base.
            file_paths: List of file paths to index.
            chunk_strategy: Chunking strategy (uses KB default if None).

        Returns:
            Dictionary with initialization stats.
        """
        # Create KB if needed
        if kb_name not in self._kb_metadata:
            await self.create_knowledge_base(
                kb_name,
                chunk_strategy=chunk_strategy or self.default_chunk_strategy,
            )

        metadata = self._kb_metadata[kb_name]
        chunker = self._get_chunker(metadata.chunk_config.strategy)
        retriever = self._get_or_create_retriever(kb_name)

        total_chunks = 0
        processed_files = 0
        errors: list[dict[str, str]] = []

        for file_path in file_paths:
            try:
                # Get file size
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

                # Parse document
                document = await self._parse_file(file_path)

                # Chunk document
                chunks = chunker.chunk(document)

                # Add to retriever
                await retriever.add_chunks(chunks)

                # Update metadata
                metadata.add_document(file_path, len(chunks), file_size)

                total_chunks += len(chunks)
                processed_files += 1

                logger.debug(f"Indexed {file_path}: {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                errors.append({
                    "file": file_path,
                    "error": str(e),
                })

        # Save updated metadata
        kb_dir = os.path.join(self.persist_directory, kb_name)
        save_metadata(metadata, kb_dir)

        return {
            "kb_name": kb_name,
            "processed_files": processed_files,
            "total_chunks": total_chunks,
            "errors": errors,
        }

    async def search(
        self,
        query: str,
        kb_name: str,
        top_k: int = 5,
        generate_answer: bool = True,
    ) -> SearchResult:
        """Search the knowledge base.

        Args:
            query: Search query.
            kb_name: Name of the knowledge base to search.
            top_k: Number of results to retrieve.
            generate_answer: Whether to generate an answer using LLM.

        Returns:
            SearchResult with retrieved chunks and optional answer.

        Raises:
            ValueError: If KB doesn't exist.
        """
        if kb_name not in self._kb_metadata:
            # Try to load from disk
            kb_dir = os.path.join(self.persist_directory, kb_name)
            metadata = load_metadata(kb_dir)
            if metadata:
                self._kb_metadata[kb_name] = metadata
            else:
                raise ValueError(f"Knowledge base not found: {kb_name}")

        metadata = self._kb_metadata[kb_name]
        retriever = self._get_or_create_retriever(kb_name)

        # Retrieve relevant chunks
        chunks = await retriever.retrieve(query, top_k=top_k)

        # Build context from chunks
        context = self._build_context(chunks)

        # Generate answer if requested
        answer = ""
        if generate_answer and chunks:
            answer = await self._generate_answer(query, context)

        return SearchResult(
            query=query,
            answer=answer,
            content=context,
            mode=metadata.retrieval_mode,
            provider=metadata.provider,
            chunks=chunks,
            metadata={
                "kb_name": kb_name,
                "top_k": top_k,
                "num_chunks": len(chunks),
                "embedding_model": metadata.embedding_info.model,
            },
        )

    async def add_document(
        self,
        kb_name: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Add a single document to an existing knowledge base.

        Args:
            kb_name: Name of the knowledge base.
            file_path: Path to the file to add.

        Returns:
            Dictionary with add stats.

        Raises:
            ValueError: If KB doesn't exist.
        """
        if kb_name not in self._kb_metadata:
            raise ValueError(f"Knowledge base not found: {kb_name}")

        metadata = self._kb_metadata[kb_name]
        chunker = self._get_chunker(metadata.chunk_config.strategy)
        retriever = self._get_or_create_retriever(kb_name)

        # Parse and chunk
        document = await self._parse_file(file_path)
        chunks = chunker.chunk(document)

        # Add to retriever
        await retriever.add_chunks(chunks)

        # Update metadata
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        metadata.add_document(file_path, len(chunks), file_size)

        # Save metadata
        kb_dir = os.path.join(self.persist_directory, kb_name)
        save_metadata(metadata, kb_dir)

        return {
            "file": file_path,
            "chunks_added": len(chunks),
        }

    async def remove_document(
        self,
        kb_name: str,
        file_path: str,
    ) -> bool:
        """Remove a document from the knowledge base.

        Args:
            kb_name: Name of the knowledge base.
            file_path: Path of the file to remove.

        Returns:
            True if document was removed.
        """
        if kb_name not in self._kb_metadata:
            return False

        metadata = self._kb_metadata[kb_name]
        retriever = self._get_or_create_retriever(kb_name)

        # Remove from retriever
        await retriever.delete_by_source(file_path)

        # Update metadata
        removed = metadata.remove_document(file_path)

        if removed:
            kb_dir = os.path.join(self.persist_directory, kb_name)
            save_metadata(metadata, kb_dir)

        return removed

    async def delete_knowledge_base(self, kb_name: str) -> bool:
        """Delete an entire knowledge base.

        Args:
            kb_name: Name of the knowledge base to delete.

        Returns:
            True if deleted.
        """
        if kb_name in self._knowledge_bases:
            await self._knowledge_bases[kb_name].clear()
            del self._knowledge_bases[kb_name]

        if kb_name in self._kb_metadata:
            del self._kb_metadata[kb_name]

        # Delete metadata file
        kb_dir = os.path.join(self.persist_directory, kb_name)
        delete_metadata(kb_dir)

        # Optionally delete the entire directory
        # import shutil
        # shutil.rmtree(kb_dir, ignore_errors=True)

        logger.info(f"Deleted KB: {kb_name}")
        return True

    def list_knowledge_bases(self) -> list[dict[str, Any]]:
        """List all knowledge bases.

        Returns:
            List of KB info dictionaries.
        """
        result = []

        for kb_name, metadata in self._kb_metadata.items():
            result.append({
                "name": metadata.name,
                "provider": metadata.provider,
                "retrieval_mode": metadata.retrieval_mode,
                "total_chunks": metadata.total_chunks,
                "document_count": len(metadata.documents),
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
                "embedding_model": metadata.embedding_info.model,
                "chunk_strategy": metadata.chunk_config.strategy,
            })

        return result

    def get_knowledge_base_info(self, kb_name: str) -> dict[str, Any] | None:
        """Get detailed info for a knowledge base.

        Args:
            kb_name: Name of the knowledge base.

        Returns:
            KB info dictionary or None if not found.
        """
        if kb_name not in self._kb_metadata:
            return None

        metadata = self._kb_metadata[kb_name]
        return metadata.to_dict()

    def _get_or_create_retriever(self, kb_name: str) -> VectorRetriever:
        """Get or create a retriever for the knowledge base.

        Args:
            kb_name: Name of the knowledge base.

        Returns:
            VectorRetriever instance.
        """
        if kb_name not in self._knowledge_bases:
            persist_path = os.path.join(self.persist_directory, kb_name)
            Path(persist_path).mkdir(parents=True, exist_ok=True)

            self._knowledge_bases[kb_name] = VectorRetriever(
                collection_name=kb_name,
                embedding_func=self.embedding_client.embed,
                persist_directory=persist_path,
            )

        return self._knowledge_bases[kb_name]

    async def _parse_file(self, file_path: str) -> Document:
        """Parse a file using the appropriate parser.

        Args:
            file_path: Path to the file.

        Returns:
            Parsed Document.

        Raises:
            ValueError: If no parser supports the file type.
        """
        for parser in self._parsers:
            if parser.supports(file_path):
                return await parser.parse(file_path)

        raise ValueError(f"No parser available for file: {file_path}")

    def _build_context(self, chunks: list[Chunk]) -> str:
        """Build context string from chunks.

        Args:
            chunks: List of chunks.

        Returns:
            Context string.
        """
        if not chunks:
            return ""

        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("source", "Unknown")
            page = chunk.metadata.get("page", "")
            page_info = f" (Page {page})" if page else ""
            parts.append(f"[{i}] Source: {source}{page_info}\n{chunk.content}")

        return "\n\n---\n\n".join(parts)

    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate an answer using LLM.

        Args:
            query: User query.
            context: Retrieved context.

        Returns:
            Generated answer.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers questions based on "
                    "the provided context. If the answer cannot be found in the "
                    "context, say so. Be concise and accurate. When citing information, "
                    "reference the source number in brackets like [1]."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ]

        response = await complete(
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        return response.content


# Singleton instance
_rag_service: RAGService | None = None


def get_rag_service(
    persist_directory: str | None = None,
    embedding_config: EmbeddingConfig | None = None,
) -> RAGService:
    """Get or create the RAG service singleton.

    Args:
        persist_directory: Directory to persist data.
        embedding_config: Embedding configuration.

    Returns:
        RAGService instance.
    """
    global _rag_service

    if _rag_service is None or persist_directory is not None:
        _rag_service = RAGService(
            persist_directory=persist_directory,
            embedding_config=embedding_config,
        )

    return _rag_service


def clear_rag_service() -> None:
    """Clear the cached RAG service."""
    global _rag_service
    _rag_service = None
