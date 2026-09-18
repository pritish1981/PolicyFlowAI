"""Short authoritative transactions for expense and assessment records."""
import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.exceptions import IdempotencyConflictError
from app.models.assessment import Assessment
from app.models.expense import Expense, ExpenseIdempotency
from app.schemas.expense import ExpenseAssessmentResponse, ExpenseCreate


def request_fingerprint(request: ExpenseCreate) -> str:
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ExpenseRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get(self, expense_id: UUID) -> Expense | None:
        with self.session_factory() as session:
            return session.scalar(select(Expense).options(selectinload(Expense.assessment))
                                  .where(Expense.id == expense_id))

    def _replay(self, key: str, fingerprint: str) -> Expense:
        with self.session_factory() as session:
            entry = session.get(ExpenseIdempotency, key)
            if entry is None:
                raise RuntimeError("idempotency insert failed without an existing key")
            if entry.request_hash != fingerprint:
                raise IdempotencyConflictError("Idempotency-Key is bound to a different payload")
            expense = session.scalar(select(Expense).options(selectinload(Expense.assessment))
                                     .where(Expense.id == entry.expense_id))
            if expense is None:
                raise RuntimeError("idempotency entry references a missing expense")
            return expense

    def create_or_get(self, request: ExpenseCreate, request_id: str,
                      key: str | None) -> tuple[Expense, bool]:
        fingerprint = request_fingerprint(request)
        if key:
            with self.session_factory() as session:
                if session.get(ExpenseIdempotency, key) is not None:
                    return self._replay(key, fingerprint), False
        expense_id = uuid4()
        expense = Expense(
            id=expense_id, thread_id=str(uuid4()), request_id=request_id,
            status="PENDING_CLARIFICATION" if request.missing_fields() else "PENDING_ASSESSMENT",
            **{name: value.value if hasattr(value, "value") else value
               for name, value in request.model_dump().items()},
        )
        try:
            with self.session_factory() as session:
                session.add(expense)
                if key:
                    session.add(ExpenseIdempotency(idempotency_key=key,
                                                   request_hash=fingerprint,
                                                   expense_id=expense_id))
                session.commit()
                session.refresh(expense)
            return expense, True
        except IntegrityError:
            if not key:
                raise
            return self._replay(key, fingerprint), False

    def clarify(self, expense_id: UUID, updates: dict) -> Expense | None:
        with self.session_factory() as session:
            expense = session.scalar(select(Expense).where(Expense.id == expense_id)
                                     .with_for_update())
            if expense is None:
                return None
            if expense.status != "PENDING_CLARIFICATION":
                raise IdempotencyConflictError("expense no longer accepts clarification")
            for name, value in updates.items():
                setattr(expense, name, value.value if hasattr(value, "value") else value)
            expense.version += 1
            expense.status = ("PENDING_CLARIFICATION" if any(
                getattr(expense, name) is None for name in ExpenseCreate.model_fields)
                else "PENDING_ASSESSMENT")
            session.commit()
            session.refresh(expense)
            return expense

    def mark_failed(self, expense_id: UUID) -> None:
        with self.session_factory() as session:
            expense = session.get(Expense, expense_id)
            if expense and expense.status == "PENDING_ASSESSMENT":
                expense.status = "ASSESSMENT_FAILED"
                session.commit()

    def retry_failed(self, expense_id: UUID) -> bool:
        with self.session_factory() as session:
            expense = session.scalar(select(Expense).where(Expense.id == expense_id)
                                     .with_for_update())
            if expense is None or expense.status != "ASSESSMENT_FAILED":
                return False
            expense.status = "PENDING_ASSESSMENT"
            session.commit()
            return True

    def save_assessment(self, result: ExpenseAssessmentResponse, rule_data: dict,
                        model_name: str | None, prompt_version: str | None) -> Assessment:
        with self.session_factory() as session:
            expense = session.scalar(select(Expense).where(Expense.id == result.expense_id)
                                     .with_for_update())
            if expense is None:
                raise RuntimeError("expense missing before assessment commit")
            if expense.status == "ASSESSED":
                stored = session.scalar(select(Assessment).where(Assessment.expense_id == expense.id))
                if stored is not None:
                    return stored
            record = Assessment(
                id=uuid4(), expense_id=expense.id, decision=result.decision.value,
                policy_rule_json=rule_data,
                citations_json=[item.model_dump(mode="json") for item in result.citations],
                policy_limit=result.policy_limit, confidence=result.confidence,
                explanation=result.explanation, next_action=result.next_action,
                model_name=model_name, prompt_version=prompt_version,
            )
            session.add(record)
            expense.status = "ASSESSED"
            session.commit()
            session.refresh(record)
            return record
