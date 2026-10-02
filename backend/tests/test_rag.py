"""
Tests for RAG pipeline: parsing, chunking, embeddings, cosine similarity, and tenant isolation.
"""

import pytest
from app.rag.chunker import chunk_document
from app.rag.embeddings import cosine_similarity, _generate_deterministic_embedding
from app.rag.parser import clean_text, parse_txt_or_md


class TestRAGParserAndChunker:
    """Test document text parsing and chunking."""

    def test_clean_text(self):
        dirty = "  Header text\r\n\r\nMultiple   spaces   here.\n\n\n\nBottom text.  "
        cleaned = clean_text(dirty)
        assert "Multiple spaces here." in cleaned
        assert "\r" not in cleaned
        assert cleaned.startswith("Header")

    def test_parse_txt_or_md(self):
        sample = b"# Company Policy\n\nAll refunds must be requested within 30 days."
        pages = parse_txt_or_md(sample)
        assert len(pages) == 1
        page_num, text = pages[0]
        assert page_num == 1
        assert "30 days" in text

    def test_chunk_document_basic(self):
        pages = [(1, "Paragraph 1: Introduction to company operations.\n\nParagraph 2: Detailed policy on refunds and guarantees.\n\nParagraph 3: Service level commitments.")]
        chunks = chunk_document(pages, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 1
        assert all(c.page_number == 1 for c in chunks)
        assert all(c.content for c in chunks)


class TestRAGEmbeddingsAndSimilarity:
    """Test vector embedding generation and cosine similarity."""

    def test_cosine_similarity_identical_vectors(self):
        v = [0.5, 0.5, 0.5, 0.5]
        score = cosine_similarity(v, v)
        assert abs(score - 1.0) < 1e-4

    def test_cosine_similarity_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        score = cosine_similarity(v1, v2)
        assert abs(score - 0.0) < 1e-4

    def test_deterministic_embedding_semantic_match(self):
        text_a = "enterprise refund cancellation policy guarantee"
        text_b = "refund policy and guarantee cancellation terms"
        text_c = "agricultural fertilizer tractor mechanical parts"

        emb_a = _generate_deterministic_embedding(text_a)
        emb_b = _generate_deterministic_embedding(text_b)
        emb_c = _generate_deterministic_embedding(text_c)

        sim_ab = cosine_similarity(emb_a, emb_b)
        sim_ac = cosine_similarity(emb_a, emb_c)

        # Semantic match should have substantially higher similarity
        assert sim_ab > sim_ac
        assert sim_ab > 0.4
