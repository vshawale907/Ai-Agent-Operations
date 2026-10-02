"""
Embedding generator and vector similarity computation for RAG.

Provides OpenAI embedding integration with deterministic offline fallback
vectorizer and cosine similarity calculation.
"""

import hashlib
import math
import re
from typing import List

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_DIM = 384


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b

    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0

    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


def _generate_deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Generate a reproducible, normalized dense float vector from text.
    
    Uses subword n-grams and hashing trick with TF weighting, producing high
    semantic alignment for matching tokens and phrases without external API calls.
    """
    if not text:
        return [0.0] * dim

    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())

    for word in words:
        # Word hash
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign * 1.5

        # Character 3-grams
        for i in range(len(word) - 2):
            trigram = word[i : i + 3]
            h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
            idx_tri = h_tri % dim
            sign_tri = 1.0 if (h_tri >> 8) % 2 == 0 else -1.0
            vec[idx_tri] += sign_tri * 0.5

    # L2 Normalization
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]

    return vec


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using Gemini, OpenAI, or deterministic fallback."""
    # Attempt Gemini first if configured
    gemini_key = (
        getattr(settings, "gemini_api_key", None)
        or getattr(settings, "GEMINI_API_KEY", "")
    )
    if gemini_key and not gemini_key.startswith("mock"):
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={gemini_key}",
                    headers={"Content-Type": "application/json"},
                    json={"content": {"parts": [{"text": text[:8000]}]}},
                )
                if res.status_code == 200:
                    data = res.json()
                    values = data.get("embedding", {}).get("values", [])
                    if values:
                        return values
        except Exception as e:
            logger.warning(f"Gemini embedding request failed, checking fallbacks: {e}")

    # Attempt OpenAI if key is configured and not mock
    api_key = getattr(settings, "openai_api_key", None) or getattr(settings, "OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("mock"):
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": text[:8000], "model": "text-embedding-3-small"},
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"OpenAI embedding request failed, using deterministic fallback: {e}")

    # Fallback deterministic vector
    return _generate_deterministic_embedding(text)


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Compute embeddings for a batch of text strings."""
    results = []
    for text in texts:
        emb = await get_embedding(text)
        results.append(emb)
    return results
