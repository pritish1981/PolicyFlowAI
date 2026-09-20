"""Credential-free Phase 005 contracts, graph, and API adapter tests."""
from decimal import Decimal
from uuid import uuid4

import pytest
from app.api.routes.reviews import get_exception_service
from app.graph.expense_graph import build_exception_graph
from app.main import app
from app.repositories.review_repository import calculate_variance
from app.schemas.review import (
    ExceptionCreate,
    ExceptionInformation,
    ExceptionOutcome,
    ExceptionReviewSummary,
    ExceptionStatus,
    ReviewAction,
)
from app.schemas.policy import PolicyCitation
from app.services.exception_service import validate_summary_citations
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import ValidationError


def test_justification_and_information_bounds():
    assert ExceptionCreate(justification="x" * 20).justification == "x" * 20
    with pytest.raises(ValidationError):
        ExceptionCreate(justification="too short")
    with pytest.raises(ValidationError):
        ExceptionInformation(information=" " * 12)
    with pytest.raises(ValidationError):
        ExceptionCreate(justification="x" * 20, unexpected=True)


def test_review_and_summary_are_strict_and_non_authoritative():
    assert ReviewAction(decision="APPROVE", comments="Accepted").decision == "APPROVE"
    for decision in ("REJECT", "REQUEST_MORE_INFORMATION"):
        assert ReviewAction(decision=decision, comments="Documented").decision == decision
    with pytest.raises(ValidationError):
        ReviewAction(decision="AUTO_APPROVE", comments="No")
    with pytest.raises(ValidationError):
        ExceptionReviewSummary(summary="Facts", recommended_decision="APPROVE")


def test_summary_citations_must_be_from_verified_assessment_evidence():
    allowed = uuid4()
    citations = [PolicyCitation(chunk_id=allowed, policy_code="POL-002", policy_version="1.0",
        section_id="limit", section_title="Limit", excerpt="INR 7000")]
    validate_summary_citations(ExceptionReviewSummary(summary="Facts",
        citation_chunk_ids=[allowed]), citations)
    with pytest.raises(ValueError, match="outside"):
        validate_summary_citations(ExceptionReviewSummary(summary="Facts",
            citation_chunk_ids=[uuid4()]), citations)


def test_decimal_variance():
    assert calculate_variance(Decimal("9500.00"), Decimal("7000.00")) == Decimal("2500.00")
    assert calculate_variance(Decimal("1.01"), Decimal("1.00")) == Decimal("0.01")
    assert calculate_variance(Decimal("9500.00"), None) is None


@pytest.mark.parametrize(("decision", "status"), [
    ("APPROVE", "APPROVED"), ("REJECT", "REJECTED"),
    ("REQUEST_MORE_INFORMATION", "MORE_INFORMATION_REQUIRED")])
def test_exception_graph_interrupt_and_same_thread_resume(decision, status):
    graph = build_exception_graph(MemorySaver())
    thread_id = "stable-thread"
    state = {"scenario": "exception_review", "exception_id": str(uuid4()),
             "expense_id": str(uuid4()), "thread_id": thread_id, "request_id": "req",
             "expense": {"amount": "9500.00"}, "decision": {"decision": "NEEDS_REVIEW"},
             "exception_justification": "Approved hotels were unavailable.",
             "variance_amount": "2500.00", "summary_status": "UNAVAILABLE",
             "review_summary": None, "citations": [], "errors": []}
    config = {"configurable": {"thread_id": thread_id}}
    interrupted = graph.invoke(state, config=config)
    assert interrupted["__interrupt__"][0].value["variance_amount"] == "2500.00"
    complete = graph.invoke(Command(resume={"decision": decision, "comments": "Accepted",
                                             "reviewer_id": "reviewer-demo"}), config=config)
    assert complete["final_status"] == status
    assert complete["reviewer_id"] == "reviewer-demo"


def test_exception_graph_rejects_non_review_assessment():
    graph = build_exception_graph(MemorySaver())
    with pytest.raises(ValueError, match="NEEDS_REVIEW"):
        graph.invoke({"decision": {"decision": "COMPLIANT"}},
                     config={"configurable": {"thread_id": "ineligible"}})


class FakeExceptionService:
    async def decide(self, exception_id, reviewer_id, action):
        return ExceptionOutcome(exception_id=exception_id, expense_id=uuid4(), thread_id="thread",
            status=ExceptionStatus.APPROVED, next_action="COMPLETE", reviewer_comments=action.comments)

    def pending(self):
        return []

    def detail(self, _exception_id):
        return None


def test_reviewer_role_and_decision_api():
    app.dependency_overrides[get_exception_service] = lambda: FakeExceptionService()
    client = TestClient(app)
    exception_id = uuid4()
    try:
        assert client.get("/api/v1/reviews/pending", headers={"X-Demo-Role": "EMPLOYEE"}).status_code == 403
        response = client.post(f"/api/v1/reviews/{exception_id}/decision",
            headers={"X-Demo-Role": "REVIEWER", "X-Demo-User": "reviewer-1"},
            json={"decision": "APPROVE", "comments": "Business justification accepted."})
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"
        assert client.post(f"/api/v1/reviews/{exception_id}/decision",
            headers={"X-Demo-Role": "REVIEWER"},
            json={"decision": "INVALID", "comments": "No"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
