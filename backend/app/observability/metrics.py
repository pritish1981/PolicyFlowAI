"""Safe metadata builders used by runtime workflow stages."""
from decimal import Decimal

from app.observability.redaction import sanitize_metadata


def retrieval_metadata(*, filters: dict, lexical_hits: list, vector_hits: list) -> dict:
    return sanitize_metadata({
        "metadata_filters": filters, "lexical_count": len(lexical_hits),
        "vector_count": len(vector_hits),
        "retrieved_chunk_ids": [str(hit.chunk_id) for hit in lexical_hits + vector_hits],
        "lexical_ranks": {str(hit.chunk_id): hit.lexical_rank for hit in lexical_hits},
        "vector_ranks": {str(hit.chunk_id): hit.vector_rank for hit in vector_hits},
    })


def ranking_metadata(hits: list, *, reranked: bool = False,
                     fallback: bool = False) -> dict:
    return sanitize_metadata({
        "reranked_count" if reranked else "fused_count": len(hits),
        "selected_chunk_ids": [str(hit.chunk_id) for hit in hits],
        "rrf_scores": {str(hit.chunk_id): hit.rrf_score for hit in hits},
        "rerank_scores": {str(hit.chunk_id): hit.rerank_score for hit in hits},
        "rerank_fallback": fallback,
    })


def citation_metadata(generated_ids: list, valid: list,
                      rejection_categories: dict[str, int] | None = None) -> dict:
    valid_ids = {str(item.chunk_id) for item in valid}
    generated = [str(item) for item in generated_ids]
    return sanitize_metadata({
        "generated_count": len(generated), "valid_count": len(valid_ids),
        "invalid_count": len([item for item in generated if item not in valid_ids]),
        "cited_chunk_ids": generated,
        "invalid_chunk_ids": [item for item in generated if item not in valid_ids],
        "rejection_categories": rejection_categories or {},
    })


def decision_metadata(*, expense_type: object, rule_type: object | None,
                      policy_limit: Decimal | None, decision: object, confidence: Decimal,
                      citation_count: int, abstention_category: str | None = None) -> dict:
    return sanitize_metadata({
        "expense_type": expense_type, "rule_type": rule_type,
        "policy_limit": policy_limit, "decision": decision, "confidence": confidence,
        "citation_count": citation_count, "abstention_category": abstention_category,
    })


def hitl_metadata(*, status: object, action: object | None = None) -> dict:
    return sanitize_metadata({"status": status, "action": action})
