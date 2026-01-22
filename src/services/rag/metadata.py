"""Knowledge Base metadata management.

Handles persistence of KB configuration and state via metadata.json files.
Each KB directory contains a metadata.json with:
- Provider/pipeline used to create the KB
- Creation and update timestamps
- Configuration (chunking, embedding, etc.)
- Document statistics
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

METADATA_FILENAME = "metadata.json"


@dataclass
class ChunkConfig:
    """Chunking configuration."""

    strategy: str = "text"  # text, semantic
    chunk_size: int = 1000
    chunk_overlap: int = 200

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EmbeddingInfo:
    """Embedding configuration snapshot."""

    model: str = "text-embedding-3-small"
    binding: str = "openai"
    dimensions: int = 1536

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingInfo":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DocumentInfo:
    """Information about an indexed document."""

    file_path: str
    file_name: str
    num_chunks: int
    added_at: str
    file_size: int = 0
    file_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentInfo":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KBMetadata:
    """Knowledge Base metadata.

    Stores all configuration and state for a knowledge base.
    Persisted as metadata.json in the KB directory.
    """

    name: str
    provider: str = "chromadb"
    retrieval_mode: str = "vector"  # vector, hybrid, graph
    created_at: str = ""
    updated_at: str = ""
    chunk_config: ChunkConfig = field(default_factory=ChunkConfig)
    embedding_info: EmbeddingInfo = field(default_factory=EmbeddingInfo)
    documents: list[DocumentInfo] = field(default_factory=list)
    total_chunks: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()

    def add_document(
        self,
        file_path: str,
        num_chunks: int,
        file_size: int = 0,
    ) -> None:
        """Record a new document.

        Args:
            file_path: Path to the document.
            num_chunks: Number of chunks created.
            file_size: File size in bytes.
        """
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1].lower()

        doc_info = DocumentInfo(
            file_path=file_path,
            file_name=file_name,
            num_chunks=num_chunks,
            added_at=datetime.utcnow().isoformat(),
            file_size=file_size,
            file_type=file_type,
        )

        # Check if document already exists (update)
        for i, doc in enumerate(self.documents):
            if doc.file_path == file_path:
                self.total_chunks -= doc.num_chunks
                self.documents[i] = doc_info
                self.total_chunks += num_chunks
                self.update_timestamp()
                return

        # New document
        self.documents.append(doc_info)
        self.total_chunks += num_chunks
        self.update_timestamp()

    def remove_document(self, file_path: str) -> bool:
        """Remove a document from tracking.

        Args:
            file_path: Path to the document.

        Returns:
            True if document was found and removed.
        """
        for i, doc in enumerate(self.documents):
            if doc.file_path == file_path:
                self.total_chunks -= doc.num_chunks
                del self.documents[i]
                self.update_timestamp()
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "provider": self.provider,
            "retrieval_mode": self.retrieval_mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chunk_config": self.chunk_config.to_dict(),
            "embedding_info": self.embedding_info.to_dict(),
            "documents": [d.to_dict() for d in self.documents],
            "total_chunks": self.total_chunks,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KBMetadata":
        """Create from dictionary."""
        chunk_config = ChunkConfig.from_dict(data.get("chunk_config", {}))
        embedding_info = EmbeddingInfo.from_dict(data.get("embedding_info", {}))
        documents = [
            DocumentInfo.from_dict(d) for d in data.get("documents", [])
        ]

        return cls(
            name=data.get("name", ""),
            provider=data.get("provider", "chromadb"),
            retrieval_mode=data.get("retrieval_mode", "vector"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            chunk_config=chunk_config,
            embedding_info=embedding_info,
            documents=documents,
            total_chunks=data.get("total_chunks", 0),
            extra=data.get("extra", {}),
        )


def save_metadata(metadata: KBMetadata, kb_dir: str | Path) -> None:
    """Save KB metadata to disk.

    Args:
        metadata: KBMetadata to save.
        kb_dir: Directory of the knowledge base.
    """
    kb_path = Path(kb_dir)
    kb_path.mkdir(parents=True, exist_ok=True)

    metadata_path = kb_path / METADATA_FILENAME

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

    logger.debug(f"Saved metadata for KB: {metadata.name}")


def load_metadata(kb_dir: str | Path) -> KBMetadata | None:
    """Load KB metadata from disk.

    Args:
        kb_dir: Directory of the knowledge base.

    Returns:
        KBMetadata if found, None otherwise.
    """
    metadata_path = Path(kb_dir) / METADATA_FILENAME

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return KBMetadata.from_dict(data)
    except Exception as e:
        logger.error(f"Failed to load metadata from {metadata_path}: {e}")
        return None


def delete_metadata(kb_dir: str | Path) -> bool:
    """Delete KB metadata file.

    Args:
        kb_dir: Directory of the knowledge base.

    Returns:
        True if deleted, False if not found.
    """
    metadata_path = Path(kb_dir) / METADATA_FILENAME

    if metadata_path.exists():
        metadata_path.unlink()
        return True
    return False


def discover_knowledge_bases(base_dir: str | Path) -> list[KBMetadata]:
    """Discover all knowledge bases in a directory.

    Scans the base directory for subdirectories with metadata.json files.

    Args:
        base_dir: Base directory to scan.

    Returns:
        List of KBMetadata for found knowledge bases.
    """
    base_path = Path(base_dir)
    knowledge_bases: list[KBMetadata] = []

    if not base_path.exists():
        return knowledge_bases

    for item in base_path.iterdir():
        if item.is_dir():
            metadata = load_metadata(item)
            if metadata:
                knowledge_bases.append(metadata)

    return knowledge_bases
