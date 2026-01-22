"""RAG Service Module.

Provides RAG (Retrieval Augmented Generation) capabilities for FinanceAI.

Features:
- Multi-provider embedding support (OpenAI, Ollama, etc.)
- Knowledge base persistence with metadata
- Configurable chunking strategies (text, semantic)
- Vector-based retrieval with ChromaDB
- Automatic KB discovery from disk

Usage:
    from src.services.rag import RAGService, get_rag_service

    # Initialize knowledge base with documents
    service = get_rag_service()
    await service.initialize("my_kb", ["document.pdf", "report.txt"])

    # Search with answer generation
    result = await service.search("What is the revenue?", "my_kb")
    print(result.answer)

    # List all knowledge bases
    kbs = service.list_knowledge_bases()

Environment Variables:
    RAG_PERSIST_DIR: Directory to persist KB data (default: ./data/rag)
"""

from .metadata import (
    ChunkConfig,
    DocumentInfo,
    EmbeddingInfo,
    KBMetadata,
    discover_knowledge_bases,
    load_metadata,
    save_metadata,
)
from .service import RAGService, clear_rag_service, get_rag_service
from .types import Chunk, Document, SearchResult

__all__ = [
    # Service
    "RAGService",
    "get_rag_service",
    "clear_rag_service",
    # Types
    "Chunk",
    "Document",
    "SearchResult",
    # Metadata
    "KBMetadata",
    "ChunkConfig",
    "EmbeddingInfo",
    "DocumentInfo",
    "load_metadata",
    "save_metadata",
    "discover_knowledge_bases",
]
