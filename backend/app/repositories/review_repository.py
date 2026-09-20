"""Authoritative exception/review transactions and projections."""
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import ExceptionIneligibleError, ReviewConflictError
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.exception_request import ExceptionRequest
from app.models.expense import Expense
from app.models.review import Review
from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.schemas.review import ExceptionStatus, ReviewDecision


def calculate_variance(amount: Decimal, policy_limit: Decimal | None) -> Decimal | None:
    return None if policy_limit is None else amount - policy_limit


class ReviewRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    def _audit(session, event_type: str, *, expense: Expense, exception_id: UUID,
               actor_id: str | None = None, review_id: UUID | None = None,
               previous: str | None = None, current: str | None = None) -> None:
        session.add(AuditEvent(id=uuid4(), event_type=event_type,
            request_id=expense.request_id, thread_id=expense.thread_id,
            expense_id=expense.id, exception_id=exception_id, review_id=review_id,
            actor_id=actor_id, metadata_json={"previous_status": previous, "new_status": current}))

    def get(self, exception_id: UUID) -> ExceptionRequest | None:
        with self.session_factory() as session:
            return session.scalar(select(ExceptionRequest).options(selectinload(ExceptionRequest.reviews))
                                  .where(ExceptionRequest.id == exception_id))

    def find_by_expense(self, expense_id: UUID) -> ExceptionRequest | None:
        with self.session_factory() as session:
            return session.scalar(select(ExceptionRequest).options(selectinload(ExceptionRequest.reviews))
                                  .where(ExceptionRequest.expense_id == expense_id))

    def append_event(self, exception_id: UUID, event_type: str, actor_id: str | None = None) -> None:
        with self.session_factory() as session:
            record = session.get(ExceptionRequest, exception_id)
            if record is None:
                return
            expense = session.get(Expense, record.expense_id)
            self._audit(session, event_type, expense=expense, exception_id=exception_id,
                        actor_id=actor_id, current=record.status)
            session.commit()

    def create(self, expense_id: UUID, justification: str) -> tuple[ExceptionRequest, bool]:
        with self.session_factory() as session:
            expense = session.scalar(select(Expense).where(Expense.id == expense_id).with_for_update())
            if expense is None:
                raise LookupError("Expense not found")
            assessment = session.scalar(select(Assessment).where(Assessment.expense_id == expense_id))
            if assessment is None or assessment.decision != "NEEDS_REVIEW":
                raise ExceptionIneligibleError("Only NEEDS_REVIEW assessments accept exceptions")
            existing = session.scalar(select(ExceptionRequest).where(ExceptionRequest.expense_id == expense_id))
            if existing is not None:
                if existing.status in (ExceptionStatus.APPROVED, ExceptionStatus.REJECTED):
                    raise ReviewConflictError("Exception is already finalized")
                return existing, False
            record = ExceptionRequest(id=uuid4(), expense_id=expense.id, assessment_id=assessment.id,
                thread_id=expense.thread_id, justification=justification,
                variance_amount=calculate_variance(expense.amount, assessment.policy_limit),
                status=ExceptionStatus.PENDING_REVIEW, summary_status="PENDING",
                information_history=[], resume_status="NOT_REQUIRED")
            session.add(record)
            expense.status = "PENDING_EXCEPTION_REVIEW"
            self._audit(session, "EXCEPTION_CREATED", expense=expense, exception_id=record.id,
                        actor_id="employee-demo", current=record.status)
            session.commit()
            session.refresh(record)
            return record, True

    def set_summary(self, exception_id: UUID, summary: dict | None) -> None:
        with self.session_factory() as session:
            record = session.get(ExceptionRequest, exception_id)
            if record:
                record.summary_json = summary
                record.summary_status = "AVAILABLE" if summary is not None else "UNAVAILABLE"
                session.commit()

    def pending(self) -> list[ExceptionRequest]:
        with self.session_factory() as session:
            return list(session.scalars(select(ExceptionRequest).where(
                ExceptionRequest.status == ExceptionStatus.PENDING_REVIEW).order_by(ExceptionRequest.created_at)))

    def decide(self, exception_id: UUID, reviewer_id: str, decision: ReviewDecision,
               comments: str) -> tuple[ExceptionRequest, Review]:
        with self.session_factory() as session:
            record = session.scalar(select(ExceptionRequest).where(ExceptionRequest.id == exception_id).with_for_update())
            if record is None:
                raise LookupError("Exception not found")
            if record.status != ExceptionStatus.PENDING_REVIEW:
                raise ReviewConflictError("Exception is not pending review")
            expense = session.get(Expense, record.expense_id)
            previous = record.status
            review = Review(id=uuid4(), exception_id=record.id, reviewer_id=reviewer_id,
                            decision=decision, comments=comments)
            session.add(review)
            if decision == ReviewDecision.APPROVE:
                record.status = ExceptionStatus.APPROVED
                expense.status = "EXCEPTION_APPROVED"
            elif decision == ReviewDecision.REJECT:
                record.status = ExceptionStatus.REJECTED
                expense.status = "EXCEPTION_REJECTED"
            else:
                record.status = ExceptionStatus.MORE_INFORMATION_REQUIRED
                expense.status = "EXCEPTION_INFORMATION_REQUIRED"
            record.resume_status = "PENDING"
            self._audit(session, "REVIEWER_ACTION", expense=expense, exception_id=record.id,
                        review_id=review.id, actor_id=reviewer_id, previous=previous, current=record.status)
            session.commit()
            session.refresh(record)
            session.refresh(review)
            return record, review

    def add_information(self, exception_id: UUID, information: str) -> ExceptionRequest:
        with self.session_factory() as session:
            record = session.scalar(select(ExceptionRequest).where(ExceptionRequest.id == exception_id).with_for_update())
            if record is None:
                raise LookupError("Exception not found")
            if record.status != ExceptionStatus.MORE_INFORMATION_REQUIRED:
                raise ReviewConflictError("Exception does not accept more information")
            expense = session.get(Expense, record.expense_id)
            record.information_history = [*record.information_history, information]
            record.status = ExceptionStatus.PENDING_REVIEW
            record.resume_status = "NOT_REQUIRED"
            expense.status = "PENDING_EXCEPTION_REVIEW"
            self._audit(session, "EXCEPTION_INFORMATION_PROVIDED", expense=expense,
                        exception_id=record.id, actor_id="employee-demo",
                        previous=ExceptionStatus.MORE_INFORMATION_REQUIRED, current=record.status)
            session.commit()
            session.refresh(record)
            return record

    def mark_resumed(self, exception_id: UUID) -> None:
        with self.session_factory() as session:
            record = session.get(ExceptionRequest, exception_id)
            if record and record.resume_status == "PENDING":
                record.resume_status = "COMPLETE"
                session.commit()

    def context(self, exception_id: UUID):
        with self.session_factory() as session:
            row = session.execute(select(ExceptionRequest, Expense, Assessment)
                .join(Expense, Expense.id == ExceptionRequest.expense_id)
                .join(Assessment, Assessment.id == ExceptionRequest.assessment_id)
                .where(ExceptionRequest.id == exception_id)).one_or_none()
            return row

    def verified_citations(self, exception_id: UUID) -> list[dict]:
        """Re-resolve stored citation identity/excerpts from authoritative RAG rows."""
        row = self.context(exception_id)
        if row is None:
            return []
        _, _, assessment = row
        stored = {str(item["chunk_id"]): item for item in assessment.citations_json}
        if not stored:
            return []
        with self.session_factory() as session:
            rows = session.execute(select(PolicyChunk, PolicyDocument).join(PolicyDocument)
                .where(PolicyChunk.id.in_([UUID(item) for item in stored]))).all()
        verified = []
        for chunk, document in rows:
            candidate = stored[str(chunk.id)]
            if (candidate.get("policy_code") == document.policy_code
                    and candidate.get("policy_version") == document.version
                    and candidate.get("section_id") == chunk.section_id):
                verified.append({"chunk_id": str(chunk.id), "policy_code": document.policy_code,
                    "policy_version": document.version, "section_id": chunk.section_id,
                    "section_title": chunk.section_title, "excerpt": chunk.content[:800]})
        return verified
