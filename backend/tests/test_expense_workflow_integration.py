"""Live PostgreSQL workflow and checkpoint smoke with no model credentials."""
import asyncio
import selectors
from decimal import Decimal
from uuid import uuid4
import pytest

from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import ModelUnavailableError
from app.db.session import SessionLocal
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.base import ProviderResult
from app.graph.expense_graph import ExpenseDependencies
from app.rag.retrieval.hybrid_retriever import HybridResults
from app.schemas.expense import Decision, ExpenseClarification, ExpenseCreate
from app.services.expense_service import ExpenseService


class UnusedProvider:
    async def generate_structured(self, **kwargs):
        raise AssertionError("no evidence must skip the model")


def _service():
    return ExpenseService(ExpenseDependencies(
        SessionLocal, ModelGateway(UnusedProvider()),
        retriever=lambda *_args, **_kwargs: HybridResults([], []),
    ), settings.database_url)


def run(coroutine):
    return asyncio.run(coroutine,
                       loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


def test_clarification_checkpoint_and_assessment_replay():
    service = _service()
    key = str(uuid4())
    payload = ExpenseCreate(expense_type="HOTEL", amount="100", currency="INR",
                            location="Delhi", travel_type="DOMESTIC", purpose="Business")
    first = run(service.create(payload, "expense-integration", key))
    assert first.missing_fields == ["receipt_available"]
    assert first.decision == Decision.INSUFFICIENT_INFORMATION
    with SessionLocal() as session:
        assert session.scalar(text("select count(*) from checkpoint.checkpoints where thread_id = :t"),
                              {"t": first.thread_id}) > 0
    resumed = run(_service().clarify(first.expense_id,
                  ExpenseClarification(receipt_available=True)))
    assert resumed.thread_id == first.thread_id
    assert resumed.decision == Decision.INSUFFICIENT_INFORMATION
    assert resumed.missing_fields == []
    replay = run(_service().create(payload, "another-request", key))
    assert replay.expense_id == first.expense_id
    assert replay.thread_id == first.thread_id
    with SessionLocal() as session:
        assert session.scalar(text("select count(*) from app.assessment where expense_id = :id"),
                              {"id": first.expense_id}) == 1


class GoldenProvider:
    async def generate_structured(self, *, messages, output_schema, model, max_output_tokens):
        import re
        del max_output_tokens
        evidence = messages[1]["content"]
        chunks = re.findall(r"chunk_id: ([\w-]+).*?section: ([^\n]+).*?content: (.*?)(?=\n\nchunk_id:|\Z)",
                            evidence, re.S)
        def source(marker):
            return next(item[0] for item in chunks if marker in item[1])
        category = ("HOTEL" if "expense_type: HOTEL" in evidence else
                    "MEAL" if "expense_type: MEAL" in evidence else "GROUND_TRANSPORTATION")
        travel = "INTERNATIONAL" if "travel_type: INTERNATIONAL" in evidence else "DOMESTIC"
        limit = ("15000" if travel == "INTERNATIONAL" else
                 "7000" if category == "HOTEL" else "1500" if category == "MEAL" else "2000")
        marker = ("international-hotel-limit" if travel == "INTERNATIONAL" else
                  "domestic-hotel-limit" if category == "HOTEL" else
                  "domestic-daily-limit" if category == "MEAL" else "airport-taxi-limit")
        unit = "PER_NIGHT" if category == "HOTEL" else "PER_DAY" if category == "MEAL" else "PER_TRIP"
        output = output_schema.model_validate({"rules": [
            {"rule_type": "AMOUNT_LIMIT", "category": category, "amount_limit": limit,
             "currency": "INR", "travel_type": travel, "unit": unit,
             "source_chunk_ids": [source(marker)]},
            {"rule_type": "RECEIPT_REQUIRED", "category": "DOCUMENTATION",
             "amount_limit": "500", "currency": "INR", "source_chunk_ids": [source("mandatory-receipt-threshold")]},
            {"rule_type": "REVIEW_REQUIRED", "category": "EXPENSE_EXCEPTION",
             "source_chunk_ids": [source("when-review-is-required")]},
        ]})
        return ProviderResult(output=output, provider="fake", model=model)


def test_live_evidence_fake_model_golden_decisions():
    service = ExpenseService(ExpenseDependencies(SessionLocal, ModelGateway(GoldenProvider())),
                             settings.database_url)
    cases = [
        ("HOTEL", "DOMESTIC", "6500", True, Decision.COMPLIANT, "7000"),
        ("HOTEL", "INTERNATIONAL", "14500", True, Decision.COMPLIANT, "15000"),
        ("HOTEL", "DOMESTIC", "9500", True, Decision.NEEDS_REVIEW, "7000"),
        ("MEAL", "DOMESTIC", "1200", True, Decision.COMPLIANT, "1500"),
        ("TAXI", "DOMESTIC", "1800", True, Decision.COMPLIANT, "2000"),
        ("TAXI", "DOMESTIC", "501", False, Decision.NON_COMPLIANT, "2000"),
    ]
    for kind, travel, amount, receipt, expected, limit in cases:
        request = ExpenseCreate(expense_type=kind, travel_type=travel, amount=amount,
                                currency="INR", location="Bengaluru", purpose="Client meeting",
                                receipt_available=receipt)
        result = run(service.create(request, str(uuid4()), str(uuid4())))
        assert result.decision == expected, (kind, travel, result.explanation, result.citations,
                                            service.repository.get(result.expense_id).assessment.policy_rule_json)
        assert result.policy_limit == Decimal(limit)
        assert len(result.citations) >= 3
        assert result.confidence == 1


def test_failed_assessment_retries_same_business_record():
    class DownProvider:
        async def generate_structured(self, **_kwargs):
            raise ConnectionError("fake outage")
    payload = ExpenseCreate(expense_type="HOTEL", amount="6500", currency="INR",
                            location="Bengaluru", travel_type="DOMESTIC",
                            purpose="Client meeting", receipt_available=True)
    key = str(uuid4())
    failing = ExpenseService(ExpenseDependencies(SessionLocal, ModelGateway(DownProvider())),
                             settings.database_url)
    with pytest.raises(ModelUnavailableError):
        run(failing.create(payload, "retry-test", key))
    from app.models.expense import ExpenseIdempotency
    with SessionLocal() as session:
        expense_id = session.get(ExpenseIdempotency, key).expense_id
    assert failing.repository.get(expense_id).status == "ASSESSMENT_FAILED"
    recovered = ExpenseService(ExpenseDependencies(SessionLocal, ModelGateway(GoldenProvider())),
                               settings.database_url)
    result = run(recovered.create(payload, "retry-test-other-id", key))
    assert result.expense_id == expense_id
    assert result.decision == Decision.COMPLIANT
