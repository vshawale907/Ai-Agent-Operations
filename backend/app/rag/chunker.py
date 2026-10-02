"""
Semantic text chunker for RAG pipeline.

Splits parsed page text into coherent chunks with overlap,
preserving page numbers and tracking token estimates.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TextChunk:
    chunk_index: int
    content: str
    page_number: Optional[int]
    token_count: int


def estimate_tokens(text: str) -> int:
    """Fast estimation of token count (~4 characters per token)."""
    return max(1, len(text) // 4)


def chunk_document(
    pages: List[Tuple[int, str]],
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> List[TextChunk]:
    """Split pages of text into overlapping TextChunks.
    
    Args:
        pages: List of (page_number, text) tuples.
        chunk_size: Target character length per chunk.
        chunk_overlap: Number of characters to overlap between adjacent chunks.
        
    Returns:
        List of TextChunk instances with preserved page metadata.
    """
    chunks: List[TextChunk] = []
    chunk_index = 0

    for page_num, text in pages:
        if not text.strip():
            continue

        # Split into paragraphs or sentences first
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph fits in chunk_size
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # If current chunk has content, record it
                if current_chunk:
                    chunks.append(
                        TextChunk(
                            chunk_index=chunk_index,
                            content=current_chunk.strip(),
                            page_number=page_num,
                            token_count=estimate_tokens(current_chunk),
                        )
                    )
                    chunk_index += 1

                    # Keep overlap from the end of current_chunk
                    if len(current_chunk) > chunk_overlap:
                        overlap_text = current_chunk[-chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # Paragraph is longer than chunk_size, split by sliding window
                    step = chunk_size - chunk_overlap
                    for i in range(0, len(para), step):
                        slice_text = para[i : i + chunk_size].strip()
                        if slice_text:
                            chunks.append(
                                TextChunk(
                                    chunk_index=chunk_index,
                                    content=slice_text,
                                    page_number=page_num,
                                    token_count=estimate_tokens(slice_text),
                                )
                            )
                            chunk_index += 1
                    current_chunk = ""

        # Flush any remaining text for this page
        if current_chunk.strip():
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    content=current_chunk.strip(),
                    page_number=page_num,
                    token_count=estimate_tokens(current_chunk),
                )
            )
            chunk_index += 1

    return chunks
