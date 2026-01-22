"""Knowledge Base API endpoints."""

import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.core.config import get_project_root
from src.services.rag import get_rag_service

router = APIRouter()

# Upload directory
UPLOAD_DIR = get_project_root() / "data" / "uploads"


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    generate_answer: bool = True


class SearchResponse(BaseModel):
    query: str
    answer: str
    sources: list[dict[str, Any]]
    num_results: int


class KnowledgeBaseInfo(BaseModel):
    name: str
    document_count: int
    description: str = ""


@router.get("")
async def list_knowledge_bases() -> list[dict[str, Any]]:
    """List all knowledge bases."""
    try:
        service = get_rag_service()
        return service.list_knowledge_bases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_knowledge_base(request: KnowledgeBaseCreate) -> dict[str, Any]:
    """Create a new empty knowledge base."""
    try:
        service = get_rag_service()
        # Initialize with empty file list
        result = await service.initialize(request.name, [])
        return {
            "name": request.name,
            "description": request.description,
            "status": "created",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kb_name}")
async def delete_knowledge_base(kb_name: str) -> dict[str, str]:
    """Delete a knowledge base."""
    try:
        service = get_rag_service()
        await service.delete_knowledge_base(kb_name)
        return {"status": "deleted", "name": kb_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_name}/upload")
async def upload_document(
    kb_name: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Upload a document to a knowledge base."""
    try:
        # Create upload directory
        kb_upload_dir = UPLOAD_DIR / kb_name
        kb_upload_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        file_path = kb_upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Add to knowledge base
        service = get_rag_service()
        result = await service.add_document(kb_name, str(file_path))

        return {
            "filename": file.filename,
            "kb_name": kb_name,
            **result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_name}/upload-multiple")
async def upload_multiple_documents(
    kb_name: str,
    files: list[UploadFile] = File(...),
) -> dict[str, Any]:
    """Upload multiple documents to a knowledge base."""
    try:
        # Create upload directory
        kb_upload_dir = UPLOAD_DIR / kb_name
        kb_upload_dir.mkdir(parents=True, exist_ok=True)

        # Save all uploaded files
        file_paths: list[str] = []
        for file in files:
            file_path = kb_upload_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append(str(file_path))

        # Initialize knowledge base with all files
        service = get_rag_service()
        result = await service.initialize(kb_name, file_paths)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kb_name}/documents/{filename}")
async def delete_document(kb_name: str, filename: str) -> dict[str, str]:
    """Delete a document from a knowledge base."""
    try:
        # Get file path
        file_path = UPLOAD_DIR / kb_name / filename

        # Remove from knowledge base
        service = get_rag_service()
        await service.remove_document(kb_name, str(file_path))

        # Delete file
        if file_path.exists():
            file_path.unlink()

        return {"status": "deleted", "filename": filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kb_name}/search")
async def search_knowledge_base(
    kb_name: str,
    request: SearchRequest,
) -> SearchResponse:
    """Search a knowledge base."""
    try:
        service = get_rag_service()
        result = await service.search(
            query=request.query,
            kb_name=kb_name,
            top_k=request.top_k,
            generate_answer=request.generate_answer,
        )

        return SearchResponse(
            query=result.query,
            answer=result.answer,
            sources=[
                {
                    "content": chunk.content[:500],
                    "source": chunk.metadata.get("source", "Unknown"),
                    "type": chunk.chunk_type,
                    "relevance": chunk.metadata.get("relevance_score", 0),
                }
                for chunk in result.chunks
            ],
            num_results=len(result.chunks),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{kb_name}/documents")
async def list_documents(kb_name: str) -> list[dict[str, Any]]:
    """List documents in a knowledge base."""
    try:
        kb_upload_dir = UPLOAD_DIR / kb_name

        if not kb_upload_dir.exists():
            return []

        documents: list[dict[str, Any]] = []
        for file_path in kb_upload_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })

        return documents

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
