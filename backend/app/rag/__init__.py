"""
RAG (Retrieval-Augmented Generation) package.

Provides document parsing, semantic chunking, vector embedding,
and tenant-isolated vector search.
"""

from app.rag.service import rag_service

__all__ = ["rag_service"]
