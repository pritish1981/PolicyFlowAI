"""Configured reranking with explicit safe fallback."""
import logging

from app.core.config import settings
from app.core.exceptions import RerankerUnavailableError
from app.rag.reranking.bge_reranker import BGEReranker
from app.rag.reranking.cohere_reranker import CohereReranker
from app.rag.retrieval.rrf import SearchHit

logger = logging.getLogger(__name__)


def get_reranker():
    if settings.rerank_provider == "cohere":
        if not settings.cohere_api_key:
            raise RerankerUnavailableError("COHERE_API_KEY is not configured")
        return CohereReranker(settings.cohere_api_key, settings.cohere_rerank_model)
    if settings.rerank_provider == "bge":
        return BGEReranker(settings.bge_rerank_model)
    if settings.rerank_provider == "rrf":
        return None
    raise RerankerUnavailableError("unsupported rerank provider")


def rerank(query: str, hits: list[SearchHit], reranker=None) -> list[SearchHit]:
    if not hits:
        return []
    try:
        selected = reranker if reranker is not None else get_reranker()
        if selected is None:
            return hits[:settings.rerank_top_k]
        return selected.rerank(query, hits, settings.rerank_top_k)
    except Exception as exc:
        if settings.rerank_fallback_to_rrf:
            logger.warning("reranker unavailable; using configured RRF fallback")
            return hits[:settings.rerank_top_k]
        if isinstance(exc, RerankerUnavailableError):
            raise
        raise RerankerUnavailableError("reranking failed") from exc
