"""Central allow-list and normalization for exported telemetry."""
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

MAX_STRING = 160
MAX_LIST = 50

_ALLOWED_KEYS = {
    "event", "stage", "outcome", "scenario", "request_id", "thread_id", "expense_id",
    "exception_id", "review_id", "status", "action", "task", "provider", "model",
    "prompt_version", "latency_ms", "duration_ms", "input_tokens", "output_tokens",
    "total_tokens", "retry_count", "validation_retry_count", "fallback_used",
    "guardrail_outcome", "error_category", "category", "region", "travel_type",
    "as_of", "metadata_filters", "lexical_count", "vector_count", "fused_count",
    "reranked_count", "generated_count", "valid_count", "invalid_count",
    "citation_valid_count", "citation_count", "selected_chunk_ids", "retrieved_chunk_ids",
    "cited_chunk_ids", "invalid_chunk_ids", "chunk_ids", "lexical_ranks", "vector_ranks",
    "rejection_categories",
    "rrf_scores", "rerank_scores", "rerank_fallback", "decision", "expense_type",
    "rule_type", "policy_limit", "confidence", "abstention_category", "evidence_status",
    "policy_code", "policy_version", "section_id", "rank", "score", "count",
}
_SENSITIVE_PARTS = {
    "api_key", "authorization", "password", "secret", "connection", "prompt", "query",
    "content", "body", "payload", "purpose", "justification", "comment",
    "reviewer_comments", "exception_information", "email", "phone", "name",
}


def sanitize_metadata(values: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values.items():
        normalized_key = str(key).lower()
        if normalized_key not in _ALLOWED_KEYS:
            continue
        normalized = _normalize(value, nested=normalized_key in {
            "metadata_filters", "lexical_ranks", "vector_ranks", "rrf_scores", "rerank_scores",
        })
        if normalized is not None:
            result[normalized_key] = normalized
    return result


def _normalize(value: object, *, nested: bool = False) -> object | None:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (UUID, Decimal, date, datetime, Enum)):
        return str(value)
    if isinstance(value, str):
        return value[:MAX_STRING]
    if isinstance(value, Mapping):
        if not nested:
            return sanitize_metadata(value)
        return {str(key)[:MAX_STRING]: _normalize(item, nested=True)
                for key, item in list(value.items())[:MAX_LIST]
                if not any(part in str(key).lower() for part in _SENSITIVE_PARTS)}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [_normalize(item, nested=True) for item in list(value)[:MAX_LIST]]
    return str(value)[:MAX_STRING]
