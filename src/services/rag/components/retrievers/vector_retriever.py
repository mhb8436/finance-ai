"""Vector-based retriever using ChromaDB."""

import asyncio
from typing import Any, Callable, Awaitable

from ..base import BaseRetriever
from ...types import Chunk


class VectorRetriever(BaseRetriever):
    """Vector retriever using ChromaDB for storage and similarity search."""

    def __init__(
        self,
        collection_name: str,
        embedding_func: Callable[[list[str]], Awaitable[list[list[float]]]],
        persist_directory: str | None = None,
    ):
        """Initialize the vector retriever.

        Args:
            collection_name: Name of the ChromaDB collection.
            embedding_func: Async function to generate embeddings.
            persist_directory: Directory to persist ChromaDB data.
        """
        self.collection_name = collection_name
        self.embedding_func = embedding_func
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    @property
    def client(self):
        """Get ChromaDB client (lazy initialization)."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ImportError(
                    "chromadb is required for vector retrieval. "
                    "Install with: pip install chromadb"
                )

            if self.persist_directory:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )
            else:
                self._client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )

        return self._client

    @property
    def collection(self):
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

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
            **kwargs: Additional parameters (e.g., where filter).

        Returns:
            List of relevant Chunk objects sorted by relevance.
        """
        # Generate query embedding
        embeddings = await self.embedding_func([query])
        query_embedding = embeddings[0]

        # Search in ChromaDB
        results = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
            **kwargs,
        )

        # Convert to Chunk objects
        chunks: list[Chunk] = []

        if results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(
                documents
            )
            distances = results["distances"][0] if results["distances"] else [0.0] * len(
                documents
            )

            for doc, meta, dist in zip(documents, metadatas, distances):
                chunk = Chunk(
                    content=doc,
                    chunk_type=meta.get("chunk_type", "text"),
                    metadata={
                        **meta,
                        "relevance_score": 1 - dist,  # Convert distance to similarity
                    },
                )
                chunks.append(chunk)

        return chunks

    async def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the retriever index.

        Args:
            chunks: Chunks to index.
        """
        if not chunks:
            return

        # Prepare data for ChromaDB
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for i, chunk in enumerate(chunks):
            documents.append(chunk.content)

            # Flatten metadata for ChromaDB (only primitive types)
            flat_meta = {
                "chunk_type": chunk.chunk_type,
            }
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    flat_meta[key] = value
                elif value is not None:
                    flat_meta[key] = str(value)

            metadatas.append(flat_meta)

            # Generate unique ID
            source = chunk.metadata.get("source", "unknown")
            chunk_idx = chunk.metadata.get("chunk_index", i)
            ids.append(f"{source}_{chunk_idx}_{i}")

        # Generate embeddings
        embeddings = await self.embedding_func(documents)

        # Add to ChromaDB
        await asyncio.to_thread(
            self.collection.add,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    async def delete_by_source(self, source: str) -> None:
        """Delete all chunks from a specific source.

        Args:
            source: Source file path to delete.
        """
        await asyncio.to_thread(
            self.collection.delete,
            where={"source": source},
        )

    async def clear(self) -> None:
        """Clear all chunks from the collection."""
        # Delete collection if it exists
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist or other error, ignore
            pass
        self._collection = None

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection stats.
        """
        return {
            "collection_name": self.collection_name,
            "count": self.collection.count(),
        }
