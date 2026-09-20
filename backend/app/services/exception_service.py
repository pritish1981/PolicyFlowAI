"""Human-owned exception workflow with short business transactions."""
import asyncio
import selectors
import sys
from contextlib import asynccontextmanager
from uuid import UUID

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.gateway.model_gateway import ModelContext, ModelGateway
from app.gateway.prompts import EXCEPTION_SUMMARY_PROMPT_VERSION, build_exception_summary_messages
from app.gateway.routing import ModelTask
from app.graph.expense_graph import build_exception_graph
from app.repositories.review_repository import ReviewRepository
from app.schemas.policy import PolicyCitation
from app.schemas.review import (
    ExceptionOutcome,
    ExceptionReviewSummary,
    ExceptionStatus,
    ReviewAction,
    ReviewDetail,
    ReviewListItem,
    ReviewResumePayload,
)


def validate_summary_citations(summary: ExceptionReviewSummary,
                               citations: list[PolicyCitation]) -> None:
    allowed = {item.chunk_id for item in citations}
    if not set(summary.citation_chunk_ids).issubset(allowed):
        raise ValueError("summary cites evidence outside the assessment")


class ExceptionService:
    def __init__(self, session_factory, gateway: ModelGateway, database_url: str):
        self.repository = ReviewRepository(session_factory)
        self.gateway = gateway
        self.database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    @asynccontextmanager
    async def _graph(self):
        async with await AsyncConnection.connect(self.database_url, autocommit=True,
            row_factory=dict_row, options="-c search_path=checkpoint,public") as connection:
            saver = AsyncPostgresSaver(connection)
            await saver.setup()
            yield build_exception_graph(saver)

    async def _execute(self, operation):
        async def run():
            async with self._graph() as graph:
                return await operation(graph)
        if sys.platform == "win32" and isinstance(asyncio.get_running_loop(), asyncio.ProactorEventLoop):
            return await asyncio.to_thread(lambda: asyncio.run(run(), loop_factory=lambda:
                asyncio.SelectorEventLoop(selectors.SelectSelector())))
        return await run()

    @staticmethod
    def _outcome(record, comments=None) -> ExceptionOutcome:
        action = ("WAIT_FOR_REVIEW" if record.status == ExceptionStatus.PENDING_REVIEW else
                  "PROVIDE_MORE_INFORMATION" if record.status == ExceptionStatus.MORE_INFORMATION_REQUIRED
                  else "COMPLETE")
        return ExceptionOutcome(exception_id=record.id, expense_id=record.expense_id,
            thread_id=record.thread_id, status=record.status, variance_amount=record.variance_amount,
            next_action=action, reviewer_comments=comments)

    async def submit(self, expense_id: UUID, justification: str) -> tuple[ExceptionOutcome, bool]:
        record, created = self.repository.create(expense_id, justification)
        row = self.repository.context(record.id)
        record, expense, assessment = row
        citations = [PolicyCitation.model_validate(item)
                     for item in self.repository.verified_citations(record.id)]
        summary = None
        try:
            result = await self.gateway.invoke_structured(task=ModelTask.EXCEPTION_REVIEW_SUMMARY,
                messages=build_exception_summary_messages({"expense": {"type": expense.expense_type,
                    "amount": str(expense.amount), "currency": expense.currency, "purpose": expense.purpose},
                    "policy_limit": str(assessment.policy_limit) if assessment.policy_limit is not None else None,
                    "variance": str(record.variance_amount) if record.variance_amount is not None else None,
                    "justification": record.justification,
                    "citations": [item.model_dump(mode="json") for item in citations]}),
                output_schema=ExceptionReviewSummary,
                context=ModelContext(request_id=expense.request_id, thread_id=expense.thread_id,
                                     prompt_version=EXCEPTION_SUMMARY_PROMPT_VERSION))
            validate_summary_citations(result.output, citations)
            summary = result.output.model_dump(mode="json")
        except Exception:
            summary = None
        self.repository.set_summary(record.id, summary)
        state = {"scenario": "exception_review", "exception_id": str(record.id),
            "expense_id": str(expense.id), "thread_id": expense.thread_id,
            "request_id": expense.request_id,
            "expense": {"expense_type": expense.expense_type, "amount": str(expense.amount),
                        "currency": expense.currency, "purpose": expense.purpose},
            "decision": {"decision": assessment.decision},
            "exception_justification": record.justification,
            "variance_amount": str(record.variance_amount) if record.variance_amount is not None else None,
            "review_summary": summary, "summary_status": "AVAILABLE" if summary else "UNAVAILABLE",
            "citations": [item.model_dump(mode="json") for item in citations], "errors": []}
        await self._execute(lambda graph: graph.ainvoke(state,
            config={"configurable": {"thread_id": expense.thread_id}}))
        self.repository.append_event(record.id, "HUMAN_REVIEW_INTERRUPTED")
        return self._outcome(self.repository.get(record.id)), created

    async def decide(self, exception_id: UUID, reviewer_id: str, action: ReviewAction) -> ExceptionOutcome:
        record, review = self.repository.decide(exception_id, reviewer_id, action.decision, action.comments)
        payload = ReviewResumePayload(exception_id=exception_id, reviewer_id=reviewer_id,
                                      decision=action.decision, comments=action.comments)
        try:
            await self._execute(lambda graph: graph.ainvoke(Command(resume=payload.model_dump(mode="json")),
                config={"configurable": {"thread_id": record.thread_id}}))
            self.repository.mark_resumed(exception_id)
            self.repository.append_event(exception_id, "WORKFLOW_RESUMED", reviewer_id)
            if record.status in (ExceptionStatus.APPROVED, ExceptionStatus.REJECTED):
                self.repository.append_event(exception_id, "EXCEPTION_FINALIZED", reviewer_id)
        except Exception:
            pass  # committed human action remains authoritative and retryable
        return self._outcome(record, review.comments)

    async def resume_committed(self, exception_id: UUID) -> ExceptionOutcome:
        """Idempotently reconcile a committed human action after checkpoint failure."""
        record = self.repository.get(exception_id)
        if record is None:
            raise LookupError("Exception not found")
        if record.resume_status == "COMPLETE":
            latest = record.reviews[-1].comments if record.reviews else None
            return self._outcome(record, latest)
        if not record.reviews:
            raise ValueError("Exception has no committed reviewer action")
        review = record.reviews[-1]
        payload = ReviewResumePayload(exception_id=exception_id, reviewer_id=review.reviewer_id,
                                      decision=review.decision, comments=review.comments)
        await self._execute(lambda graph: graph.ainvoke(Command(resume=payload.model_dump(mode="json")),
            config={"configurable": {"thread_id": record.thread_id}}))
        self.repository.mark_resumed(exception_id)
        self.repository.append_event(exception_id, "WORKFLOW_RESUMED", review.reviewer_id)
        if record.status in (ExceptionStatus.APPROVED, ExceptionStatus.REJECTED):
            self.repository.append_event(exception_id, "EXCEPTION_FINALIZED", review.reviewer_id)
        return self._outcome(record, review.comments)

    async def information(self, exception_id: UUID, information: str) -> ExceptionOutcome:
        record = self.repository.add_information(exception_id, information)
        row = self.repository.context(exception_id)
        _, expense, assessment = row
        state = {"scenario": "exception_review", "exception_id": str(record.id),
            "expense_id": str(expense.id), "thread_id": record.thread_id, "request_id": expense.request_id,
            "expense": {"expense_type": expense.expense_type, "amount": str(expense.amount),
                        "currency": expense.currency, "purpose": expense.purpose},
            "decision": {"decision": assessment.decision}, "exception_justification": record.justification,
            "variance_amount": str(record.variance_amount) if record.variance_amount is not None else None,
            "review_summary": record.summary_json, "summary_status": record.summary_status,
            "citations": assessment.citations_json, "errors": []}
        await self._execute(lambda graph: graph.ainvoke(state,
            config={"configurable": {"thread_id": record.thread_id}}))
        self.repository.append_event(record.id, "HUMAN_REVIEW_INTERRUPTED")
        return self._outcome(record)

    def pending(self) -> list[ReviewListItem]:
        return [self._detail(record, detail=False) for record in self.repository.pending()]

    def detail(self, exception_id: UUID) -> ReviewDetail | None:
        record = self.repository.get(exception_id)
        return None if record is None else self._detail(record, detail=True)

    def _detail(self, record, detail: bool):
        row = self.repository.context(record.id)
        _, expense, assessment = row
        base = dict(exception_id=record.id, expense_id=expense.id, expense_type=expense.expense_type,
            amount=expense.amount, currency=expense.currency, policy_limit=assessment.policy_limit,
            variance_amount=record.variance_amount, justification=record.justification,
            created_at=record.created_at.isoformat())
        if not detail:
            return ReviewListItem(**base)
        latest = record.reviews[-1].comments if record.reviews else None
        return ReviewDetail(**base, thread_id=record.thread_id, status=record.status,
            purpose=expense.purpose, location=expense.location, summary_status=record.summary_status,
            review_summary=record.summary_json,
            citations=[PolicyCitation.model_validate(item)
                       for item in self.repository.verified_citations(record.id)],
            information_history=record.information_history, latest_reviewer_comments=latest)
