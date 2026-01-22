"""Retrievers Module.

Provides different retrieval strategies:
- VectorRetriever: Pure vector similarity search (ChromaDB)
- HybridRetriever: Combined vector + BM25 keyword search

Usage:
    from src.services.rag.components.retrievers import VectorRetriever, HybridRetriever

    # Vector-only retrieval
    retriever = VectorRetriever(
        collection_name="my_kb",
        embedding_func=embedding_client.embed,
    )

    # Hybrid retrieval (better recall)
    retriever = HybridRetriever(
        collection_name="my_kb",
        embedding_func=embedding_client.embed,
        alpha=0.5,  # Balance between vector and BM25
    )
"""

from .hybrid_retriever import BM25Index, HybridRetriever
from .vector_retriever import VectorRetriever

__all__ = [
    "VectorRetriever",
    "HybridRetriever",
    "BM25Index",
]
