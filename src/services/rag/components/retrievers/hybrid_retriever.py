"""Hybrid retriever combining vector search with BM25 keyword search.

Provides better recall than pure vector search by combining:
1. Dense retrieval (vector similarity via ChromaDB)
2. Sparse retrieval (BM25 keyword matching)

The results are combined using Reciprocal Rank Fusion (RRF).
"""

import asyncio
import math
import re
from collections import defaultdict
from typing import Any, Awaitable, Callable

from ..base import BaseRetriever
from ...types import Chunk


class BM25Index:
    """Simple BM25 index for keyword-based retrieval.

    Implements the Okapi BM25 ranking function for text retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 index.

        Args:
            k1: Term frequency saturation parameter.
            b: Document length normalization parameter.
        """
        self.k1 = k1
        self.b = b

        # Index structures
        self._documents: dict[str, Chunk] = {}  # doc_id -> chunk
        self._doc_lengths: dict[str, int] = {}  # doc_id -> length
        self._avg_doc_length: float = 0.0
        self._doc_count: int = 0

        # Inverted index: term -> {doc_id: term_freq}
        self._inverted_index: dict[str, dict[str, int]] = defaultdict(dict)

        # Document frequency: term -> num_docs_containing_term
        self._doc_freq: dict[str, int] = defaultdict(int)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into terms.

        Simple tokenization with lowercasing and alphanumeric filtering.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens.
        """
        # Lowercase and split on non-alphanumeric (keep Korean characters)
        text = text.lower()
        tokens = re.findall(r"[\w가-힣]+", text)
        return tokens

    def add_document(self, doc_id: str, chunk: Chunk) -> None:
        """Add a document to the index.

        Args:
            doc_id: Document identifier.
            chunk: Chunk to index.
        """
        tokens = self._tokenize(chunk.content)
        doc_length = len(tokens)

        # Store document
        self._documents[doc_id] = chunk
        self._doc_lengths[doc_id] = doc_length

        # Update document count and average length
        old_total = self._avg_doc_length * self._doc_count
        self._doc_count += 1
        self._avg_doc_length = (old_total + doc_length) / self._doc_count

        # Count term frequencies
        term_freqs: dict[str, int] = defaultdict(int)
        for token in tokens:
            term_freqs[token] += 1

        # Update inverted index
        for term, freq in term_freqs.items():
            self._inverted_index[term][doc_id] = freq
            self._doc_freq[term] += 1

    def remove_document(self, doc_id: str) -> None:
        """Remove a document from the index.

        Args:
            doc_id: Document identifier to remove.
        """
        if doc_id not in self._documents:
            return

        chunk = self._documents[doc_id]
        tokens = self._tokenize(chunk.content)

        # Count term frequencies for this document
        term_freqs: dict[str, int] = defaultdict(int)
        for token in tokens:
            term_freqs[token] += 1

        # Update inverted index
        for term, freq in term_freqs.items():
            if doc_id in self._inverted_index[term]:
                del self._inverted_index[term][doc_id]
                self._doc_freq[term] -= 1

                # Clean up empty entries
                if self._doc_freq[term] == 0:
                    del self._doc_freq[term]
                    del self._inverted_index[term]

        # Update document count and average length
        doc_length = self._doc_lengths[doc_id]
        old_total = self._avg_doc_length * self._doc_count
        self._doc_count -= 1

        if self._doc_count > 0:
            self._avg_doc_length = (old_total - doc_length) / self._doc_count
        else:
            self._avg_doc_length = 0.0

        # Remove document
        del self._documents[doc_id]
        del self._doc_lengths[doc_id]

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Search the index.

        Args:
            query: Search query.
            top_k: Number of results to return.

        Returns:
            List of (doc_id, score) tuples sorted by score descending.
        """
        if self._doc_count == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Calculate BM25 scores
        scores: dict[str, float] = defaultdict(float)

        for term in query_tokens:
            if term not in self._inverted_index:
                continue

            # IDF component
            doc_freq = self._doc_freq[term]
            idf = math.log(
                (self._doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1
            )

            # Score each document containing this term
            for doc_id, term_freq in self._inverted_index[term].items():
                doc_length = self._doc_lengths[doc_id]
                length_norm = 1 - self.b + self.b * (doc_length / self._avg_doc_length)

                # BM25 TF component
                tf = (term_freq * (self.k1 + 1)) / (
                    term_freq + self.k1 * length_norm
                )

                scores[doc_id] += idf * tf

        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def clear(self) -> None:
        """Clear the index."""
        self._documents.clear()
        self._doc_lengths.clear()
        self._inverted_index.clear()
        self._doc_freq.clear()
        self._doc_count = 0
        self._avg_doc_length = 0.0

    @property
    def count(self) -> int:
        """Get document count."""
        return self._doc_count


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining vector and BM25 search.

    Uses Reciprocal Rank Fusion (RRF) to combine results from:
    1. Dense retrieval (vector similarity via ChromaDB)
    2. Sparse retrieval (BM25 keyword matching)

    Attributes:
        alpha: Weight for vector results (1-alpha for BM25).
        rrf_k: RRF constant (typically 60).
    """

    def __init__(
        self,
        collection_name: str,
        embedding_func: Callable[[list[str]], Awaitable[list[list[float]]]],
        persist_directory: str | None = None,
        alpha: float = 0.5,
        rrf_k: int = 60,
    ):
        """Initialize the hybrid retriever.

        Args:
            collection_name: Name of the ChromaDB collection.
            embedding_func: Async function to generate embeddings.
            persist_directory: Directory to persist ChromaDB data.
            alpha: Weight for vector results (0.0-1.0).
            rrf_k: RRF constant for score combination.
        """
        self.collection_name = collection_name
        self.embedding_func = embedding_func
        self.persist_directory = persist_directory
        self.alpha = alpha
        self.rrf_k = rrf_k

        # ChromaDB for vector search
        self._client = None
        self._collection = None

        # BM25 for keyword search
        self._bm25_index = BM25Index()

        # Document ID mapping
        self._chunk_to_id: dict[str, Chunk] = {}

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
        mode: str = "hybrid",
        **kwargs: Any,
    ) -> list[Chunk]:
        """Retrieve relevant chunks using hybrid search.

        Args:
            query: Search query.
            top_k: Number of results to return.
            mode: Search mode ("hybrid", "vector", "bm25").
            **kwargs: Additional parameters.

        Returns:
            List of relevant Chunk objects sorted by relevance.
        """
        if mode == "vector":
            return await self._vector_search(query, top_k)
        elif mode == "bm25":
            return self._bm25_search(query, top_k)
        else:
            return await self._hybrid_search(query, top_k)

    async def _vector_search(self, query: str, top_k: int) -> list[Chunk]:
        """Perform vector similarity search."""
        # Generate query embedding
        embeddings = await self.embedding_func([query])
        query_embedding = embeddings[0]

        # Search in ChromaDB
        results = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to Chunk objects
        chunks: list[Chunk] = []

        if results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)
            distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)

            for doc, meta, dist in zip(documents, metadatas, distances):
                chunk = Chunk(
                    content=doc,
                    chunk_type=meta.get("chunk_type", "text"),
                    metadata={
                        **meta,
                        "relevance_score": 1 - dist,
                        "retrieval_method": "vector",
                    },
                )
                chunks.append(chunk)

        return chunks

    def _bm25_search(self, query: str, top_k: int) -> list[Chunk]:
        """Perform BM25 keyword search."""
        results = self._bm25_index.search(query, top_k)

        chunks: list[Chunk] = []
        for doc_id, score in results:
            if doc_id in self._chunk_to_id:
                chunk = self._chunk_to_id[doc_id]
                # Create new chunk with updated metadata
                new_chunk = Chunk(
                    content=chunk.content,
                    chunk_type=chunk.chunk_type,
                    metadata={
                        **chunk.metadata,
                        "relevance_score": score,
                        "retrieval_method": "bm25",
                    },
                )
                chunks.append(new_chunk)

        return chunks

    async def _hybrid_search(self, query: str, top_k: int) -> list[Chunk]:
        """Perform hybrid search with RRF fusion."""
        # Get more results from each method for better fusion
        fetch_k = min(top_k * 3, 50)

        # Run both searches
        vector_results = await self._vector_search(query, fetch_k)
        bm25_results = self._bm25_search(query, fetch_k)

        # Create rank dictionaries
        vector_ranks: dict[str, int] = {}
        bm25_ranks: dict[str, int] = {}
        all_chunks: dict[str, Chunk] = {}

        for rank, chunk in enumerate(vector_results):
            doc_id = self._get_chunk_id(chunk)
            vector_ranks[doc_id] = rank
            all_chunks[doc_id] = chunk

        for rank, chunk in enumerate(bm25_results):
            doc_id = self._get_chunk_id(chunk)
            bm25_ranks[doc_id] = rank
            if doc_id not in all_chunks:
                all_chunks[doc_id] = chunk

        # Calculate RRF scores
        rrf_scores: dict[str, float] = {}

        for doc_id in all_chunks:
            vector_score = 0.0
            bm25_score = 0.0

            if doc_id in vector_ranks:
                vector_score = 1.0 / (self.rrf_k + vector_ranks[doc_id])

            if doc_id in bm25_ranks:
                bm25_score = 1.0 / (self.rrf_k + bm25_ranks[doc_id])

            # Weighted combination
            rrf_scores[doc_id] = self.alpha * vector_score + (1 - self.alpha) * bm25_score

        # Sort by RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Build result chunks
        chunks: list[Chunk] = []
        for doc_id, score in sorted_results[:top_k]:
            chunk = all_chunks[doc_id]
            # Create new chunk with RRF score
            new_chunk = Chunk(
                content=chunk.content,
                chunk_type=chunk.chunk_type,
                metadata={
                    **chunk.metadata,
                    "relevance_score": score,
                    "retrieval_method": "hybrid",
                    "in_vector": doc_id in vector_ranks,
                    "in_bm25": doc_id in bm25_ranks,
                },
            )
            chunks.append(new_chunk)

        return chunks

    def _get_chunk_id(self, chunk: Chunk) -> str:
        """Generate a consistent ID for a chunk."""
        source = chunk.metadata.get("source", "unknown")
        chunk_idx = chunk.metadata.get("chunk_index", 0)
        # Use content hash for deduplication
        content_hash = hash(chunk.content) % 10000000
        return f"{source}_{chunk_idx}_{content_hash}"

    async def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to both vector and BM25 indices.

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
            # Generate unique ID
            source = chunk.metadata.get("source", "unknown")
            chunk_idx = chunk.metadata.get("chunk_index", i)
            doc_id = f"{source}_{chunk_idx}_{i}"

            documents.append(chunk.content)

            # Flatten metadata for ChromaDB
            flat_meta = {"chunk_type": chunk.chunk_type}
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    flat_meta[key] = value
                elif value is not None:
                    flat_meta[key] = str(value)

            metadatas.append(flat_meta)
            ids.append(doc_id)

            # Add to BM25 index
            self._bm25_index.add_document(doc_id, chunk)
            self._chunk_to_id[doc_id] = chunk

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
        # Delete from ChromaDB
        await asyncio.to_thread(
            self.collection.delete,
            where={"source": source},
        )

        # Delete from BM25 index
        to_remove = [
            doc_id for doc_id, chunk in self._chunk_to_id.items()
            if chunk.metadata.get("source") == source
        ]

        for doc_id in to_remove:
            self._bm25_index.remove_document(doc_id)
            del self._chunk_to_id[doc_id]

    async def clear(self) -> None:
        """Clear all data from both indices."""
        # Clear ChromaDB
        self.client.delete_collection(self.collection_name)
        self._collection = None

        # Clear BM25
        self._bm25_index.clear()
        self._chunk_to_id.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get retriever statistics.

        Returns:
            Dictionary with stats.
        """
        return {
            "collection_name": self.collection_name,
            "vector_count": self.collection.count(),
            "bm25_count": self._bm25_index.count,
            "alpha": self.alpha,
            "rrf_k": self.rrf_k,
        }
