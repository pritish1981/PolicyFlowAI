"""Evaluator-only retrieval compositions; production settings are never mutated."""
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Callable

from app.core.config import settings
from app.rag.embeddings.embedding_provider import embed_texts
from app.rag.reranking import rerank
from app.rag.retrieval.hybrid_retriever import (
    build_filters, policy_qa_filters, retrieve,
)
from app.rag.retrieval.rrf import SearchHit, fuse
from app.rag.retrieval.vector_retriever import vector_search


@dataclass(frozen=True)
class StrategyResult:
    strategy: str
    hits: list[SearchHit]
    latency_ms: float
    fallback: bool = False
    available: bool = True


def run_strategy(strategy: str, query: str, session_factory: Callable, *,
                 category: str | None = None, region: str | None = None,
                 travel_type: str | None = None, as_of: date | None = None,
                 reranker: object | None = None) -> StrategyResult:
    started = perf_counter()
    current_date = as_of or date.today()
    if strategy == "vector":
        vector = embed_texts([query])[0]
        eligibility = build_filters(category, region, travel_type, None, current_date)
        hits = vector_search(vector, eligibility, session_factory, settings.retrieval_top_n)
        return StrategyResult(strategy, hits, (perf_counter() - started) * 1000)
    stages = retrieve(query, session_factory,
                      filters=policy_qa_filters(category, region, current_date),
                      travel_type=travel_type)
    fused = fuse([stages.lexical_hits, stages.vector_hits],
                 settings.rrf_k, settings.retrieval_top_n)
    if strategy == "hybrid":
        return StrategyResult(strategy, fused, (perf_counter() - started) * 1000)
    if strategy != "hybrid_rerank":
        raise ValueError(f"unknown retrieval strategy: {strategy}")
    ranked = rerank(query, fused, reranker)
    fallback = bool(ranked and all(hit.rerank_score is None for hit in ranked))
    return StrategyResult(strategy, ranked, (perf_counter() - started) * 1000,
                          fallback=fallback, available=not fallback)


def ranked_policy_ids(hits: list[SearchHit]) -> list[str]:
    # Preserve one identifier per ranked chunk. Repeated policy identifiers are
    # intentional because Precision@5 evaluates each returned evidence chunk.
    return [hit.policy_code for hit in hits]
