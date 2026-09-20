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


class ExpenseState(TypedDict, total=False):
    """Compact persisted expense path; authoritative money stays in app.expense."""
    scenario: Literal["expense_assessment", "exception_review"]
    expense_id: str
    thread_id: str
    request_id: str
    expense: dict[str, Any]
    assessment_date: str
    missing_fields: list[str]
    hits: list[str]
    rules: dict[str, Any] | None
    citations: list[dict[str, Any]]
    decision: dict[str, Any]
    model_name: str | None
    exception_id: str
    exception_justification: str
    variance_amount: str | None
    review_summary: dict[str, Any] | None
    summary_status: str
    reviewer_decision: str
    reviewer_comments: str
    reviewer_id: str
    requires_human: bool
    final_status: str
    errors: list[str]
