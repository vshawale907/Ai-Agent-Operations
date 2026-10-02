"""
RAG Service — Ingestion, Tenant-Isolated Storage, and Semantic Retrieval.

Enforces strict tenant isolation (user_id ownership), semantic cosine ranking,
keyword boosting, and rich source citation formatting.
"""

import re
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models.document import Document, DocumentChunk
from app.rag.chunker import chunk_document
from app.rag.embeddings import cosine_similarity, get_embedding
from app.rag.parser import parse_document

logger = get_logger(__name__)


class RAGService:
    """Production-grade Document Ingestion & RAG Retrieval Engine."""

    async def ingest_document(
        self,
        db: AsyncSession,
        user_id: int,
        filename: str,
        file_type: str,
        file_bytes: bytes,
    ) -> Document:
        """Parse, chunk, embed, and store a document with full user isolation."""
        logger.info(f"Ingesting document '{filename}' for user_id={user_id} ({len(file_bytes)} bytes)")

        # Create base Document record
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type.lower().replace(".", ""),
            file_size=len(file_bytes),
            status="processing",
            chunk_count=0,
        )
        db.add(doc)
        await db.flush()

        try:
            # 1. Parse text by pages
            pages = parse_document(file_bytes, filename, file_type)
            if not pages:
                raise ValueError("Could not extract any readable text from document.")

            # 2. Chunk text
            text_chunks = chunk_document(pages, chunk_size=650, chunk_overlap=120)
            if not text_chunks:
                raise ValueError("Document contains no parseable text chunks.")

            # 3. Embed chunks and save
            for tc in text_chunks:
                emb = await get_embedding(tc.content)
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    user_id=user_id,
                    chunk_index=tc.chunk_index,
                    content=tc.content,
                    page_number=tc.page_number,
                    token_count=tc.token_count,
                    embedding=emb,
                )
                db.add(chunk_record)

            doc.chunk_count = len(text_chunks)
            doc.status = "ready"
            await db.commit()
            await db.refresh(doc)
            logger.info(f"Successfully ingested '{filename}' with {len(text_chunks)} chunks.")
            return doc

        except Exception as e:
            logger.error(f"Failed to ingest document '{filename}': {e}")
            doc.status = "failed"
            doc.error_message = str(e)
            await db.commit()
            raise e

    async def search_documents(
        self,
        db: AsyncSession,
        user_id: int,
        query: str,
        top_k: int = 4,
        min_score: float = 0.15,
    ) -> List[Dict[str, Any]]:
        """Search user's documents using hybrid vector similarity + keyword boosting.
        
        Strictly restricts search to document chunks where chunk.user_id == user_id.
        """
        logger.info(f"RAG search query='{query[:60]}' user_id={user_id}")

        # Compute query embedding
        query_emb = await get_embedding(query)
        query_words = set(re.findall(r"\w{3,}", query.lower()))

        # Query all chunks belonging to this user
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.user_id == user_id, Document.status == "ready")
        )
        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            logger.info(f"No active documents found for user_id={user_id}")
            return []

        scored_chunks = []
        for chunk, doc_filename in rows:
            # Vector cosine similarity
            v_score = cosine_similarity(query_emb, chunk.embedding or [])

            # Keyword overlap boost (BM25-style signal)
            chunk_words = set(re.findall(r"\w{3,}", chunk.content.lower()))
            overlap = len(query_words.intersection(chunk_words))
            k_score = min(0.35, overlap * 0.1) if query_words else 0.0

            total_score = (0.75 * v_score) + (0.25 * k_score)

            if total_score >= min_score:
                page_str = f"Page {chunk.page_number}" if chunk.page_number else "Section"
                scored_chunks.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": doc_filename,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "score": round(float(total_score), 4),
                    "citation": f"{doc_filename} ({page_str}, Chunk #{chunk.chunk_index + 1})",
                })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_chunks[:top_k]
        logger.info(f"RAG search found {len(top_results)} relevant chunks (top score: {top_results[0]['score'] if top_results else 'N/A'})")
        return top_results

    async def list_documents(self, db: AsyncSession, user_id: int) -> List[Document]:
        """List all documents owned by user."""
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_document(self, db: AsyncSession, user_id: int, doc_id: int) -> Optional[Document]:
        """Get document details with chunks by ID, ensuring user ownership."""
        stmt = (
            select(Document)
            .where(Document.id == doc_id, Document.user_id == user_id)
            .options(selectinload(Document.chunks))
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def delete_document(self, db: AsyncSession, user_id: int, doc_id: int) -> bool:
        """Delete document and its chunks, verifying user ownership."""
        stmt = select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        result = await db.execute(stmt)
        doc = result.scalars().first()
        if not doc:
            return False

        await db.delete(doc)
        await db.commit()
        logger.info(f"Deleted document id={doc_id} for user_id={user_id}")
        return True

    async def seed_sample_documents(self, db: AsyncSession, user_id: int) -> None:
        """Seed realistic company operational policies if user has no documents."""
        stmt = select(Document.id).where(Document.user_id == user_id)
        result = await db.execute(stmt)
        if result.first():
            return  # Already has documents

        logger.info(f"Seeding standard operational business documents for user_id={user_id}...")

        samples = [
            (
                "Enterprise_Refund_and_Return_Policy.md",
                "md",
                """# Enterprise Refund & Cancellation Policy

## 1. Overview & Scope
This policy governs all software licenses, cloud platform subscriptions, and automated intelligence services provided to enterprise and mid-market accounts.

## 2. Standard Software Licenses
- **30-Day Evaluation Guarantee**: Annual enterprise software agreements can be cancelled within thirty (30) calendar days of initial procurement with a full 100% refund.
- **Prorated Cancellations**: Cancellations after 30 days are subject to a standard thirty percent (30%) administrative processing fee, with remaining unused prepaid months returned on a prorated basis.
- **Consumption-based Cloud Credits**: Any consumed API credits or specialized compute capacity are non-refundable once utilized.

## 3. SLA Breach Remedies
In the event of an unplanned platform outage exceeding 99.9% uptime commitments within a calendar month:
- Outage between 0.1% - 1.0%: 10% monthly service credit applied to the next billing cycle.
- Outage exceeding 1.0%: 25% monthly service credit or direct wire refund upon written request.

## 4. Refund Approval Hierarchy
- Refunds under $5,000 USD may be authorized directly by Tier 2 Support Team Leads.
- Refunds between $5,000 and $25,000 USD require written authorization from the Director of Customer Success.
- Refunds exceeding $25,000 USD require Chief Financial Officer (CFO) sign-off.
""",
            ),
            (
                "Sales_Strategy_and_Territory_Plan_2025.md",
                "md",
                """# Global Sales Strategy & Regional Expansion Plan (2025)

## 1. Executive Direction
Our strategic imperative for 2025 centers on expanding enterprise software margins and accelerating market penetration across North America and Europe while establishing a high-growth hub in Asia Pacific.

## 2. Regional Analysis & Targets
- **North America**: Continues to be our primary revenue anchor (~45% of total volume). Focus is shifting from new logo acquisition to expanding Annual Contract Value (ACV) through our Security and Cloud AI suites.
- **Europe**: Strong performance in enterprise finance and healthcare. Recent regulatory compliance updates (GDPR, EU AI Act) have generated increased demand for our Security & Compliance Pack.
- **Asia Pacific (APAC)**: High expansion opportunity. Although currently generating 18% of global revenue, customer acquisition velocity grew by 24% year-over-year. The average order value in APAC is $76.97.
- **Latin America**: Emerging test market focusing on entry-level Operations Automation tools.

## 3. Mitigating Revenue Declines
When quarterly declines are observed in specific hardware or legacy platform segments:
1. Sales teams must immediately initiate customer engagement reviews with accounts at risk of churn.
2. Bundle underperforming SKUs with high-margin AI Suite add-ons.
3. Offer flexible quarterly payment schedules rather than demanding upfront annual prepayments.
""",
            ),
            (
                "Customer_Support_SLA_and_Operations.md",
                "md",
                """# Customer Support Operations & SLA Standards

## 1. Support Tiers & Priority Levels
- **P1 (Critical Outage)**: System completely unavailable or critical transaction failure affecting revenue. Initial response time: < 15 minutes. Resolution target: < 4 hours.
- **P2 (High Impact)**: Core functionality degraded with significant business impact. Initial response time: < 1 hour. Resolution target: < 12 hours.
- **P3 (Medium Impact)**: Non-critical feature disruption with operational workaround available. Initial response time: < 4 hours. Resolution target: < 48 hours.
- **P4 (General Inquiry)**: How-to questions, feature requests, documentation clarifications. Initial response time: < 24 hours.

## 2. Customer Health & Churn Risk Triggers
Support tickets are monitored as a leading indicator for customer churn risk:
- Accounts logging three (3) or more P1/P2 tickets within a 30-day window are automatically flagged as **High Churn Risk**.
- The Account Executive and Customer Success Manager are automatically alerted within 2 hours of a churn risk flag.
- Escalated accounts receive dedicated engineering triage and executive check-in within 5 business days.
""",
            ),
        ]

        for filename, ext, content in samples:
            await self.ingest_document(
                db=db,
                user_id=user_id,
                filename=filename,
                file_type=ext,
                file_bytes=content.encode("utf-8"),
            )

        logger.info(f"Successfully seeded {len(samples)} sample business documents.")


# Singleton instance
rag_service = RAGService()
