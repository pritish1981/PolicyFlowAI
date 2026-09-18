"""Multi-policy eligibility and bounded source coverage tests."""
from datetime import date
from uuid import uuid4

from app.rag.retrieval.hybrid_retriever import HybridResults
from app.rag.retrieval.rrf import SearchHit
from app.schemas.expense import ExpenseCreate
from app.services.expense_evidence import gather_expense_evidence


class IdentityReranker:
    def rerank(self, query, hits, top_k):
        return hits[:top_k]


def test_expense_evidence_keeps_limit_receipt_and_review_sources():
    seen = []
    codes = {"HOTEL": "POL-002", "DOCUMENTATION": "POL-005",
             "EXPENSE_EXCEPTION": "POL-006"}

    def retriever(query, session_factory, *, filters, travel_type):
        del session_factory
        seen.append((filters.category, filters.region, filters.status, filters.as_of, travel_type))
        hit = SearchHit(uuid4(), codes[filters.category], "1.0", filters.category,
                        filters.category, f"{filters.category} INR 500 rule")
        return HybridResults([hit], [hit])

    expense = ExpenseCreate(expense_type="HOTEL", amount="6500", currency="INR",
                            location="Bengaluru", travel_type="DOMESTIC",
                            purpose="Client meeting", receipt_available=True)
    evidence = gather_expense_evidence(expense, lambda: None,
                                       assessment_date=date(2026, 9, 17),
                                       retriever=retriever, reranker=IdentityReranker())
    assert [item[0] for item in seen] == ["HOTEL", "DOCUMENTATION", "EXPENSE_EXCEPTION"]
    assert all(item[1:] == ("INDIA", "ACTIVE", date(2026, 9, 17), "DOMESTIC") for item in seen)
    assert {hit.policy_code for hit in evidence.reranked_hits} == set(codes.values())
    assert len(evidence.lexical_hits) == len(evidence.vector_hits) == 3
    assert all(hit.rrf_score is not None for hit in evidence.fused_hits)
