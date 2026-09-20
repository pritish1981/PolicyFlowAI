"""Live PostgreSQL business/checkpoint proof for Phase 005 HITL."""
import asyncio
import selectors
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import ReviewConflictError
from app.core.exceptions import ExceptionIneligibleError
from app.db.session import SessionLocal, engine
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.base import ProviderResult
from app.models.assessment import Assessment
from app.models.expense import Expense
from app.schemas.review import ExceptionReviewSummary, ReviewAction
from app.services.exception_service import ExceptionService
from app.api.routes.reviews import get_exception_service
from app.main import app


class SummaryProvider:
    async def generate_structured(self, *, output_schema, model, **_kwargs):
        assert output_schema is ExceptionReviewSummary
        return ProviderResult(output=output_schema(summary="Neutral exception facts.",
            key_facts=["Amount exceeds the evidenced limit."],
            risk_or_attention_points=["Reviewer must decide."], citation_chunk_ids=[]),
            provider="fake", model=model)


def run(coroutine):
    return asyncio.run(coroutine,
        loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def make_case():
    expense_id, assessment_id = uuid4(), uuid4()
    thread_id = str(uuid4())
    with SessionLocal() as session:
        citation = session.execute(text("SELECT c.id, d.policy_code, d.version, c.section_id, "
            "c.section_title, c.content FROM rag.policy_chunk c JOIN rag.policy_document d "
            "ON d.id=c.document_id WHERE d.status='ACTIVE' LIMIT 1")).mappings().one()
        session.add(Expense(id=expense_id, thread_id=thread_id, request_id=str(uuid4()),
            expense_type="HOTEL", amount=Decimal("9500.00"), currency="INR",
            location="Bengaluru", travel_type="DOMESTIC", purpose="Client conference",
            receipt_available=True, status="ASSESSED"))
        session.add(Assessment(id=assessment_id, expense_id=expense_id, decision="NEEDS_REVIEW",
            policy_rule_json={}, citations_json=[{"chunk_id": str(citation["id"]),
                "policy_code": citation["policy_code"], "policy_version": citation["version"],
                "section_id": citation["section_id"], "section_title": citation["section_title"],
                "excerpt": citation["content"][:600]}], policy_limit=Decimal("7000.00"),
            confidence=Decimal("1"), explanation="Human exception review is required.",
            next_action="SUBMIT_EXCEPTION_JUSTIFICATION", model_name="fake",
            prompt_version="expense-rule-v1"))
        session.commit()
    return expense_id, thread_id


def cleanup(expense_id, thread_id):
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM app.audit_event WHERE expense_id=:id"), {"id": expense_id})
        connection.execute(text("DELETE FROM app.review WHERE exception_id IN "
                                "(SELECT id FROM app.exception_request WHERE expense_id=:id)"), {"id": expense_id})
        connection.execute(text("DELETE FROM app.exception_request WHERE expense_id=:id"), {"id": expense_id})
        connection.execute(text("DELETE FROM app.assessment WHERE expense_id=:id"), {"id": expense_id})
        connection.execute(text("DELETE FROM app.expense WHERE id=:id"), {"id": expense_id})
        for table in ("checkpoint_writes", "checkpoints", "checkpoint_blobs"):
            connection.execute(text(f"DELETE FROM checkpoint.{table} WHERE thread_id=:thread"),
                               {"thread": thread_id})


def service():
    return ExceptionService(SessionLocal, ModelGateway(SummaryProvider()), settings.database_url)


@pytest.mark.parametrize(("decision", "expected"),
    [("APPROVE", "APPROVED"), ("REJECT", "REJECTED")])
def test_live_interrupt_reload_and_final_decision(decision, expected):
    expense_id, thread_id = make_case()
    try:
        outcome, created = run(service().submit(expense_id,
            "Approved hotels were unavailable near the conference venue."))
        assert created and outcome.status == "PENDING_REVIEW"
        assert outcome.variance_amount == Decimal("2500.00")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM checkpoint.checkpoints "
                                          "WHERE thread_id=:thread"), {"thread": thread_id}) > 0
        detail = service().detail(outcome.exception_id)
        assert detail.thread_id == thread_id
        assert detail.summary_status == "AVAILABLE"
        assert len(detail.citations) == 1 and detail.citations[0].excerpt
        finalized = run(service().decide(outcome.exception_id, "reviewer-live",
            ReviewAction(decision=decision, comments="Human reviewer decision.")))
        assert finalized.status == expected
        with pytest.raises(ReviewConflictError):
            run(service().decide(outcome.exception_id, "reviewer-duplicate",
                ReviewAction(decision=decision, comments="Duplicate decision.")))
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT decision FROM app.assessment WHERE expense_id=:id"),
                                     {"id": expense_id}) == "NEEDS_REVIEW"
            assert connection.scalar(text("SELECT count(*) FROM app.review WHERE exception_id=:id"),
                                     {"id": outcome.exception_id}) == 1
            assert connection.scalar(text("SELECT count(*) FROM app.audit_event WHERE exception_id=:id"),
                                     {"id": outcome.exception_id}) >= 4
    finally:
        cleanup(expense_id, thread_id)


def test_live_only_needs_review_is_eligible():
    expense_id, thread_id = make_case()
    try:
        with engine.begin() as connection:
            connection.execute(text("UPDATE app.assessment SET decision='COMPLIANT' WHERE expense_id=:id"),
                               {"id": expense_id})
        with pytest.raises(ExceptionIneligibleError):
            service().repository.create(expense_id, "A sufficiently long justification for review.")
    finally:
        cleanup(expense_id, thread_id)


def test_live_concurrent_review_allows_one_authoritative_action():
    expense_id, thread_id = make_case()
    try:
        outcome, _ = run(service().submit(expense_id,
            "Approved hotels were unavailable near the conference venue."))
        def decide(value):
            return service().repository.decide(outcome.exception_id, f"reviewer-{value}",
                ReviewAction(decision=value, comments="Concurrent human action.").decision,
                "Concurrent human action.")
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(decide, value) for value in ("APPROVE", "REJECT")]
            results = []
            for future in futures:
                try:
                    results.append(future.result()[0].status)
                except ReviewConflictError:
                    results.append("CONFLICT")
        assert "CONFLICT" in results
        assert sum(item in ("APPROVED", "REJECTED") for item in results) == 1
    finally:
        cleanup(expense_id, thread_id)


def test_live_summary_failure_does_not_block_human_review():
    class DownProvider:
        async def generate_structured(self, **_kwargs):
            raise ConnectionError("synthetic outage")
    expense_id, thread_id = make_case()
    try:
        down = ExceptionService(SessionLocal, ModelGateway(DownProvider()), settings.database_url)
        outcome, _ = run(down.submit(expense_id,
            "Approved hotels were unavailable near the conference venue."))
        assert outcome.status == "PENDING_REVIEW"
        assert down.detail(outcome.exception_id).summary_status == "UNAVAILABLE"
    finally:
        cleanup(expense_id, thread_id)


def test_live_committed_action_can_reconcile_resume_without_duplicate_review():
    expense_id, thread_id = make_case()
    try:
        active = service()
        outcome, _ = run(active.submit(expense_id,
            "Approved hotels were unavailable near the conference venue."))
        original_execute = active._execute
        async def fail_resume(_operation):
            raise ConnectionError("synthetic checkpoint outage")
        active._execute = fail_resume
        committed = run(active.decide(outcome.exception_id, "reviewer-reconcile",
            ReviewAction(decision="APPROVE", comments="Committed before resume.")))
        assert committed.status == "APPROVED"
        assert active.repository.get(outcome.exception_id).resume_status == "PENDING"
        reconciled = service()
        run(reconciled.resume_committed(outcome.exception_id))
        assert reconciled.repository.get(outcome.exception_id).resume_status == "COMPLETE"
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM app.review WHERE exception_id=:id"),
                                     {"id": outcome.exception_id}) == 1
        active._execute = original_execute
    finally:
        cleanup(expense_id, thread_id)


def test_live_request_more_information_round_trip():
    expense_id, thread_id = make_case()
    try:
        outcome, _ = run(service().submit(expense_id,
            "The conference venue had no hotel within the standard policy limit."))
        requested = run(service().decide(outcome.exception_id, "reviewer-live",
            ReviewAction(decision="REQUEST_MORE_INFORMATION", comments="Provide approval evidence.")))
        assert requested.status == "MORE_INFORMATION_REQUIRED"
        pending = run(service().information(outcome.exception_id,
            "Manager approval reference is SYNTHETIC-APPROVAL-001."))
        assert pending.status == "PENDING_REVIEW"
        final = run(service().decide(outcome.exception_id, "reviewer-live",
            ReviewAction(decision="APPROVE", comments="Additional information accepted.")))
        assert final.status == "APPROVED"
        assert len(service().detail(outcome.exception_id).information_history) == 1
    finally:
        cleanup(expense_id, thread_id)


def test_live_exception_review_api_round_trip():
    expense_id, thread_id = make_case()
    app.dependency_overrides[get_exception_service] = service
    client = TestClient(app)
    try:
        created = client.post(f"/api/v1/expenses/{expense_id}/exceptions",
            headers={"X-Demo-Role": "EMPLOYEE"},
            json={"justification": "Approved hotels were unavailable near the venue."})
        assert created.status_code == 201
        exception_id = created.json()["exception_id"]
        replay = client.post(f"/api/v1/expenses/{expense_id}/exceptions",
            headers={"X-Demo-Role": "EMPLOYEE"},
            json={"justification": "Approved hotels were unavailable near the venue."})
        assert replay.status_code == 200
        queue = client.get("/api/v1/reviews/pending", headers={"X-Demo-Role": "REVIEWER"})
        assert any(item["exception_id"] == exception_id for item in queue.json())
        detail = client.get(f"/api/v1/reviews/{exception_id}",
                            headers={"X-Demo-Role": "REVIEWER"})
        assert detail.status_code == 200 and detail.json()["variance_amount"] == "2500.00"
        requested = client.post(f"/api/v1/reviews/{exception_id}/decision",
            headers={"X-Demo-Role": "REVIEWER", "X-Demo-User": "reviewer-api"},
            json={"decision": "REQUEST_MORE_INFORMATION", "comments": "Provide manager approval."})
        assert requested.json()["status"] == "MORE_INFORMATION_REQUIRED"
        follow_up = client.post(f"/api/v1/exceptions/{exception_id}/information",
            headers={"X-Demo-Role": "EMPLOYEE"},
            json={"information": "Synthetic manager approval reference supplied."})
        assert follow_up.json()["status"] == "PENDING_REVIEW"
        approved = client.post(f"/api/v1/reviews/{exception_id}/decision",
            headers={"X-Demo-Role": "REVIEWER", "X-Demo-User": "reviewer-api"},
            json={"decision": "APPROVE", "comments": "Information accepted."})
        assert approved.json()["status"] == "APPROVED"
        expense = client.get(f"/api/v1/expenses/{expense_id}")
        assert expense.json()["decision"] == "NEEDS_REVIEW"
        assert expense.json()["exception"]["status"] == "APPROVED"
        conflict = client.post(f"/api/v1/reviews/{exception_id}/decision",
            headers={"X-Demo-Role": "REVIEWER"},
            json={"decision": "REJECT", "comments": "Conflicting action."})
        assert conflict.status_code == 409
    finally:
        app.dependency_overrides.clear()
        cleanup(expense_id, thread_id)
