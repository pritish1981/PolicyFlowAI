"""Live PostgreSQL business truth and idempotency verification."""
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import IdempotencyConflictError
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import Decision, ExpenseAssessmentResponse, ExpenseCreate

_root = Path(__file__).resolve().parents[2]
_database_url = dotenv_values(_root / ".env").get("DATABASE_URL")
if not _database_url:
    pytest.skip("Live integration requires project DATABASE_URL", allow_module_level=True)

engine = create_engine(_database_url, pool_pre_ping=True)
repository = ExpenseRepository(sessionmaker(bind=engine))


def test_expense_idempotency_clarification_and_assessment():
    from uuid import uuid4
    key = f"expense-repo-test-{uuid4()}"
    intake = ExpenseCreate(expense_type="HOTEL", amount="6500.00", currency="INR",
                           location="Bengaluru", travel_type="DOMESTIC",
                           receipt_available=True)
    expense = None
    try:
        expense, created = repository.create_or_get(intake, "request-1", key)
        assert created and expense.status == "PENDING_CLARIFICATION"
        assert expense.amount == Decimal("6500.00")
        replay, created = repository.create_or_get(intake, "request-2", key)
        assert not created and replay.id == expense.id
        with pytest.raises(IdempotencyConflictError):
            repository.create_or_get(intake.model_copy(update={"amount": Decimal("9500")}),
                                     "request-3", key)

        continued = repository.clarify(expense.id, {"purpose": "Client meeting"})
        assert continued.status == "PENDING_ASSESSMENT"
        assert continued.thread_id == expense.thread_id
        response = ExpenseAssessmentResponse(
            expense_id=expense.id, thread_id=expense.thread_id, request_id="request-1",
            decision=Decision.COMPLIANT, policy_limit=Decimal("7000"),
            confidence=Decimal("1"), explanation="Evidence supports the standard limit.",
        )
        repository.save_assessment(response, {"rules": []}, "fake-model", "expense-rule-v1")
        stored = repository.get(expense.id)
        assert stored.status == "ASSESSED"
        assert stored.assessment.decision == Decision.COMPLIANT.value
        assert stored.assessment.policy_limit == Decimal("7000")
    finally:
        if expense is not None:
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM app.expense_idempotency WHERE expense_id=:id"), {"id": expense.id})
                connection.execute(text("DELETE FROM app.assessment WHERE expense_id=:id"), {"id": expense.id})
                connection.execute(text("DELETE FROM app.expense WHERE id=:id"), {"id": expense.id})


def test_concurrent_same_key_creates_one_expense():
    from uuid import uuid4
    key = f"expense-concurrent-test-{uuid4()}"
    intake = ExpenseCreate(expense_type="TAXI", amount="1500", currency="INR",
                           location="Bengaluru", travel_type="DOMESTIC",
                           purpose="Airport to client", receipt_available=True)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(repository.create_or_get, intake, f"request-{i}", key)
                       for i in range(2)]
            results = [future.result() for future in futures]
        assert results[0][0].id == results[1][0].id
        assert sum(created for _, created in results) == 1
    finally:
        with engine.begin() as connection:
            expense_id = connection.scalar(text(
                "SELECT expense_id FROM app.expense_idempotency WHERE idempotency_key=:key"),
                {"key": key})
            if expense_id:
                connection.execute(text("DELETE FROM app.expense_idempotency WHERE idempotency_key=:key"), {"key": key})
                connection.execute(text("DELETE FROM app.expense WHERE id=:id"), {"id": expense_id})
