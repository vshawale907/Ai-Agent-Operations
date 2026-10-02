"""
Documents API routes for RAG document management and vector retrieval.

Supports multipart upload (PDF, TXT, MD, DOCX), tenant-isolated listing,
chunk inspection, deletion, and on-demand search.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.user import User
from app.rag.service import rag_service
from app.services.auth_service import get_current_user

router = APIRouter()


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: str


class SearchQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4


@router.get("", response_model=Dict[str, Any])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents owned by the authenticated user."""
    # Ensure sample documents exist for a great out-of-the-box experience
    await rag_service.seed_sample_documents(db, current_user.id)
    docs = await rag_service.list_documents(db, current_user.id)

    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "chunk_count": d.chunk_count,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else "",
            }
            for d in docs
        ]
    }


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and ingest a document (PDF, TXT, Markdown, DOCX) into the vector store."""
    filename = file.filename or "uploaded_document.txt"
    file_ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    allowed = {"pdf", "txt", "md", "markdown", "docx", "doc", "csv", "json"}
    if file_ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{file_ext}'. Allowed formats: {', '.join(allowed)}",
        )

    # Read bytes
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > 15 * 1024 * 1024:  # 15MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum permitted limit of 15MB.",
        )

    try:
        doc = await rag_service.ingest_document(
            db=db,
            user_id=current_user.id,
            filename=filename,
            file_type=file_ext,
            file_bytes=content,
        )
        return {
            "message": "Document successfully parsed, chunked, and embedded into vector store.",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details and extracted chunks."""
    doc = await rag_service.get_document(db, current_user.id, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
        "chunks": [
            {
                "chunk_id": c.id,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "token_count": c.token_count,
                "content_preview": c.content[:160] + "..." if len(c.content) > 160 else c.content,
            }
            for c in doc.chunks
        ],
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all its vector chunks."""
    deleted = await rag_service.delete_document(db, current_user.id, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )
    return {"message": "Document and associated embeddings successfully deleted."}


@router.post("/search")
async def search_documents(
    payload: SearchQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform direct semantic vector search against user documents."""
    results = await rag_service.search_documents(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        top_k=payload.top_k or 4,
    )
    return {"query": payload.query, "count": len(results), "results": results}


@router.post("/seed")
async def seed_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly seed standard company policy documents."""
    await rag_service.seed_sample_documents(db, current_user.id)
    return {"message": "Standard operational documents successfully seeded."}
