"""Test RAG System Integration."""

import pytest
import os
import tempfile
from pathlib import Path

from src.services.rag import RAGService, get_rag_service
from src.services.rag.types import Document, Chunk


class TestRAGTypes:
    """Test RAG data types."""

    def test_document_creation(self):
        """Test Document creation."""
        doc = Document(
            content="Test content",
            file_path="test.txt",
            metadata={"key": "value"},
        )
        assert doc.content == "Test content"
        assert doc.file_path == "test.txt"
        assert doc.metadata["key"] == "value"

    def test_chunk_creation(self):
        """Test Chunk creation."""
        chunk = Chunk(
            content="Chunk content",
            chunk_type="text",
            metadata={"source": "test.txt", "page": 1},
        )
        assert chunk.content == "Chunk content"
        assert chunk.chunk_type == "text"
        assert chunk.metadata["source"] == "test.txt"


class TestRAGService:
    """Test RAG Service functionality."""

    def test_service_singleton(self):
        """Test RAG service singleton."""
        service1 = get_rag_service()
        service2 = get_rag_service()
        assert service1 is service2

    def test_service_initialization(self):
        """Test service initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = RAGService(persist_directory=tmpdir)
            assert service.persist_directory == tmpdir
            assert service.embedding_client is not None

    def test_list_knowledge_bases_empty(self):
        """Test listing empty knowledge bases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = RAGService(persist_directory=tmpdir)
            kbs = service.list_knowledge_bases()
            assert isinstance(kbs, list)

    @pytest.mark.asyncio
    async def test_create_knowledge_base(self):
        """Test creating a knowledge base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = RAGService(persist_directory=tmpdir)
            metadata = await service.create_knowledge_base("test_kb")

            assert metadata.name == "test_kb"
            assert "test_kb" in [kb["name"] for kb in service.list_knowledge_bases()]

    @pytest.mark.asyncio
    async def test_delete_knowledge_base(self):
        """Test deleting a knowledge base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = RAGService(persist_directory=tmpdir)
            await service.create_knowledge_base("test_kb")

            result = await service.delete_knowledge_base("test_kb")
            assert result is True
            assert "test_kb" not in [kb["name"] for kb in service.list_knowledge_bases()]


class TestChunkers:
    """Test chunking functionality."""

    def test_text_chunker_import(self):
        """Test TextChunker can be imported."""
        from src.services.rag.components.chunkers import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20

    def test_text_chunker_basic(self):
        """Test basic text chunking."""
        from src.services.rag.components.chunkers import TextChunker

        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        doc = Document(
            content="This is a test document. " * 10,
            file_path="test.txt",
        )

        chunks = chunker.chunk(doc)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestParsers:
    """Test parser functionality."""

    def test_text_parser_import(self):
        """Test TextParser can be imported."""
        from src.services.rag.components.parsers import TextParser

        parser = TextParser()
        assert parser.supports("test.txt")
        assert parser.supports("test.md")
        assert not parser.supports("test.pdf")

    @pytest.mark.asyncio
    async def test_text_parser_parse(self):
        """Test parsing a text file."""
        from src.services.rag.components.parsers import TextParser

        parser = TextParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content.")
            f.flush()

            try:
                doc = await parser.parse(f.name)
                assert doc.content == "This is test content."
                assert doc.file_path == f.name
            finally:
                os.unlink(f.name)


class TestRetrievers:
    """Test retriever functionality."""

    def test_vector_retriever_import(self):
        """Test VectorRetriever can be imported."""
        from src.services.rag.components.retrievers import VectorRetriever

        # Just test import works
        assert VectorRetriever is not None


class TestRAGTool:
    """Test RAG tool for agents."""

    def test_tool_definitions(self):
        """Test RAG tool definitions."""
        from src.tools.rag_tool import RAG_TOOL_DEFINITIONS

        assert len(RAG_TOOL_DEFINITIONS) == 2

        tool_names = [t["function"]["name"] for t in RAG_TOOL_DEFINITIONS]
        assert "search_knowledge_base" in tool_names
        assert "list_knowledge_bases" in tool_names

    def test_tool_functions(self):
        """Test RAG tool functions mapping."""
        from src.tools.rag_tool import RAG_TOOL_FUNCTIONS

        assert "search_knowledge_base" in RAG_TOOL_FUNCTIONS
        assert "list_knowledge_bases" in RAG_TOOL_FUNCTIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
