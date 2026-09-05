"""Thin wrapper around Google's Gemini Embedding API.

Swapped from Voyage: Voyage's free tier caps at 3 requests/minute
without a payment method on file, which broke even a single batched
call. Gemini's free tier gives 10M tokens/minute with no card
required, and we're already using Gemini for generation -- one less
provider to manage.
"""

import numpy as np
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.gemini_api_key)

EMBED_MODEL = "models/gemini-embedding-001"
OUTPUT_DIM = 1024  # must match the `vector(1024)` column in schema.sql


def _normalize(vector: list[float]) -> list[float]:
    """gemini-embedding-001 only auto-normalizes at its full 3072-dim
    output. Since we request a reduced dimension (1024) for a smaller
    pgvector column, we must L2-normalize manually or cosine similarity
    search quality silently degrades."""
    arr = np.array(vector)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm > 0 else vector


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts (indexing time)."""
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=EMBED_MODEL,
            content=text,
            task_type="retrieval_document",
            output_dimensionality=OUTPUT_DIM,
        )
        embeddings.append(_normalize(result["embedding"]))
    return embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single user question (query time)."""
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type="retrieval_query",
        output_dimensionality=OUTPUT_DIM,
    )
    return _normalize(result["embedding"])