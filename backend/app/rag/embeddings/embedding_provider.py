"""Lazy local embedding adapter shared by ingestion and retrieval."""
from functools import lru_cache
from typing import Sequence
from app.core.config import settings


@lru_cache(maxsize=2)
def _model(name: str):
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=name)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed text with the configured local model and verify vector dimensions."""
    vectors = [vector.tolist() for vector in _model(settings.embedding_model).embed(list(texts))]
    if any(len(vector) != settings.embedding_dimension for vector in vectors):
        raise ValueError("embedding model dimension does not match database schema")
    return vectors
