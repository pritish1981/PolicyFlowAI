"""Minimal FRD-compatible state for the Phase 003 Policy Q&A graph."""
from datetime import date
from typing import Any, Literal, TypedDict
from uuid import UUID

from app.rag.citations.validator import Citation
from app.rag.retrieval.hybrid_retriever import MetadataFilters
from app.rag.retrieval.rrf import SearchHit


class PolicyQAState(TypedDict, total=False):
    request_id: str
    thread_id: str
    scenario: Literal["policy_qa"]
    user_query: str
    category: str | None
    region: str | None
    assessment_date: date
    metadata_filters: MetadataFilters
    lexical_hits: list[SearchHit]
    vector_hits: list[SearchHit]
    fused_hits: list[SearchHit]
    reranked_hits: list[SearchHit]
    citation_chunk_ids: list[UUID]
    citations: list[Citation]
    answer: str
    evidence_status: str
    model_usage: dict[str, Any]
    rerank_fallback: bool
    errors: list[str]
