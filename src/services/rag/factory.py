"""RAG Pipeline Factory.

Provides factory functions for creating RAG pipelines with different
configurations. Supports lazy loading of heavy dependencies.

Supported Pipelines:
- vector: Basic vector retrieval with ChromaDB (default)
- hybrid: Vector + BM25 keyword search (coming soon)
- lightrag: Knowledge graph based retrieval (coming soon)

Usage:
    from src.services.rag.factory import get_pipeline, list_pipelines

    # Get default pipeline
    pipeline = get_pipeline("vector", kb_dir="/path/to/kb")

    # List available pipelines
    available = list_pipelines()
"""

import logging
from typing import Any, Callable, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class RAGPipeline(Protocol):
    """Protocol for RAG pipelines.

    All pipeline implementations should follow this interface
    for compatibility with the RAG service.
    """

    name: str

    async def initialize(self, file_paths: list[str]) -> dict[str, Any]:
        """Initialize the pipeline with documents."""
        ...

    async def search(
        self,
        query: str,
        top_k: int = 5,
        **kwargs,
    ) -> dict[str, Any]:
        """Search the pipeline."""
        ...

    async def add_document(self, file_path: str) -> dict[str, Any]:
        """Add a document to the pipeline."""
        ...

    async def remove_document(self, file_path: str) -> bool:
        """Remove a document from the pipeline."""
        ...


# Pipeline registry with lazy loaders
_PIPELINE_REGISTRY: dict[str, Callable[..., Any]] = {}
_INITIALIZED = False


def _init_pipelines() -> None:
    """Initialize the pipeline registry with lazy loaders."""
    global _INITIALIZED

    if _INITIALIZED:
        return

    def _create_vector_pipeline(kb_dir: str, **kwargs) -> Any:
        """Create a vector-based pipeline (ChromaDB)."""
        from .service import RAGService

        return RAGService(persist_directory=kb_dir, **kwargs)

    def _create_hybrid_pipeline(kb_dir: str, **kwargs) -> Any:
        """Create a hybrid pipeline (Vector + BM25)."""
        # TODO: Implement hybrid pipeline
        logger.warning("Hybrid pipeline not yet implemented, falling back to vector")
        from .service import RAGService

        return RAGService(persist_directory=kb_dir, **kwargs)

    def _create_lightrag_pipeline(kb_dir: str, **kwargs) -> Any:
        """Create a LightRAG pipeline (knowledge graph)."""
        # TODO: Implement LightRAG integration
        logger.warning("LightRAG pipeline not yet implemented, falling back to vector")
        from .service import RAGService

        return RAGService(persist_directory=kb_dir, **kwargs)

    _PIPELINE_REGISTRY.update({
        "vector": _create_vector_pipeline,
        "chromadb": _create_vector_pipeline,  # Alias
        "hybrid": _create_hybrid_pipeline,
        "lightrag": _create_lightrag_pipeline,
        "graph": _create_lightrag_pipeline,  # Alias
    })

    _INITIALIZED = True
    logger.debug(f"Initialized pipeline registry: {list(_PIPELINE_REGISTRY.keys())}")


def get_pipeline(
    name: str = "vector",
    kb_dir: str = "./data/rag",
    **kwargs,
) -> Any:
    """Get or create a RAG pipeline.

    Args:
        name: Pipeline name (vector, hybrid, lightrag).
        kb_dir: Base directory for the knowledge base.
        **kwargs: Additional arguments passed to the pipeline.

    Returns:
        RAG pipeline instance.

    Raises:
        ValueError: If pipeline name is not supported.
    """
    _init_pipelines()

    if name not in _PIPELINE_REGISTRY:
        raise ValueError(
            f"Unknown pipeline: {name}. "
            f"Available: {list(_PIPELINE_REGISTRY.keys())}"
        )

    factory = _PIPELINE_REGISTRY[name]
    return factory(kb_dir=kb_dir, **kwargs)


def list_pipelines() -> list[dict[str, Any]]:
    """List available pipelines.

    Returns:
        List of pipeline info dictionaries.
    """
    _init_pipelines()

    return [
        {
            "name": "vector",
            "aliases": ["chromadb"],
            "description": "Vector-based retrieval using ChromaDB",
            "status": "stable",
        },
        {
            "name": "hybrid",
            "aliases": [],
            "description": "Hybrid retrieval combining vector and BM25 keyword search",
            "status": "planned",
        },
        {
            "name": "lightrag",
            "aliases": ["graph"],
            "description": "Knowledge graph based retrieval using LightRAG",
            "status": "planned",
        },
    ]


def register_pipeline(
    name: str,
    factory: Callable[..., Any],
    aliases: list[str] | None = None,
) -> None:
    """Register a custom pipeline factory.

    Args:
        name: Pipeline name.
        factory: Factory function that creates the pipeline.
        aliases: Optional list of aliases for the pipeline.
    """
    _init_pipelines()

    _PIPELINE_REGISTRY[name] = factory
    for alias in aliases or []:
        _PIPELINE_REGISTRY[alias] = factory

    logger.info(f"Registered pipeline: {name}")


class PipelineBuilder:
    """Builder for composing custom RAG pipelines.

    Provides a fluent API for building pipelines with custom components.

    Example:
        pipeline = (
            PipelineBuilder("my_pipeline")
            .with_parser(PDFParser())
            .with_chunker(SemanticChunker())
            .with_retriever(VectorRetriever())
            .build()
        )
    """

    def __init__(self, name: str):
        """Initialize the builder.

        Args:
            name: Pipeline name.
        """
        self.name = name
        self._parsers: list[Any] = []
        self._chunker: Any = None
        self._retriever: Any = None
        self._embedding_client: Any = None

    def with_parser(self, parser: Any) -> "PipelineBuilder":
        """Add a parser to the pipeline.

        Args:
            parser: Parser instance.

        Returns:
            Self for chaining.
        """
        self._parsers.append(parser)
        return self

    def with_chunker(self, chunker: Any) -> "PipelineBuilder":
        """Set the chunker for the pipeline.

        Args:
            chunker: Chunker instance.

        Returns:
            Self for chaining.
        """
        self._chunker = chunker
        return self

    def with_retriever(self, retriever: Any) -> "PipelineBuilder":
        """Set the retriever for the pipeline.

        Args:
            retriever: Retriever instance.

        Returns:
            Self for chaining.
        """
        self._retriever = retriever
        return self

    def with_embedding_client(self, client: Any) -> "PipelineBuilder":
        """Set the embedding client.

        Args:
            client: Embedding client instance.

        Returns:
            Self for chaining.
        """
        self._embedding_client = client
        return self

    def build(self) -> dict[str, Any]:
        """Build the pipeline configuration.

        Returns:
            Dictionary with pipeline components.
        """
        return {
            "name": self.name,
            "parsers": self._parsers,
            "chunker": self._chunker,
            "retriever": self._retriever,
            "embedding_client": self._embedding_client,
        }
