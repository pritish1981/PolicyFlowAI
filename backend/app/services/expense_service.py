"""Short business transactions around the durable expense graph."""
import asyncio
import selectors
import sys
from contextlib import asynccontextmanager
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.gateway.prompts import EXPENSE_RULE_PROMPT_VERSION
from app.graph.graph import ExpenseDependencies, build_expense_graph
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import (Decision, ExpenseAssessmentResponse, ExpenseClarification,
                                 ExpenseCreate)
from app.schemas.policy import PolicyCitation


def _payload(expense) -> dict:
    return {name: getattr(expense, name) for name in ExpenseCreate.model_fields}


class ExpenseService:
    def __init__(self, dependencies: ExpenseDependencies, database_url: str):
        self.dependencies = dependencies
        self.repository = ExpenseRepository(dependencies.session_factory)
        self.database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    @asynccontextmanager
    async def _graph(self):
        async with await AsyncConnection.connect(
            self.database_url, autocommit=True, row_factory=dict_row,
            options="-c search_path=checkpoint,public",
        ) as connection:
            saver = AsyncPostgresSaver(connection)
            await saver.setup()
            yield build_expense_graph(self.dependencies, saver)

    async def _invoke_graph(self, payload: dict, thread_id: str) -> dict:
        async def execute():
            async with self._graph() as graph:
                return await graph.ainvoke(payload,
                    config={"configurable": {"thread_id": thread_id}})

        if sys.platform == "win32" and isinstance(asyncio.get_running_loop(),
                                                    asyncio.ProactorEventLoop):
            return await asyncio.to_thread(lambda: asyncio.run(
                execute(), loop_factory=lambda: asyncio.SelectorEventLoop(
                    selectors.SelectSelector())))
        return await execute()

    def _response(self, expense) -> ExpenseAssessmentResponse:
        expense = self.repository.get(expense.id)
        missing = ExpenseCreate.model_validate(_payload(expense)).missing_fields()
        if expense.assessment is not None:
            record = expense.assessment
            return ExpenseAssessmentResponse(
                expense_id=expense.id, thread_id=expense.thread_id, request_id=expense.request_id,
                decision=Decision(record.decision), policy_limit=record.policy_limit,
                confidence=record.confidence, explanation=record.explanation,
                citations=[PolicyCitation.model_validate(item) for item in record.citations_json],
                next_action=record.next_action,
            )
        if missing:
            return ExpenseAssessmentResponse(
                expense_id=expense.id, thread_id=expense.thread_id, request_id=expense.request_id,
                decision=Decision.INSUFFICIENT_INFORMATION, confidence=0,
                explanation="Complete the missing expense fields before assessment.",
                next_action="PROVIDE_CLARIFICATION", missing_fields=missing,
            )
        return ExpenseAssessmentResponse(
            expense_id=expense.id, thread_id=expense.thread_id, request_id=expense.request_id,
            decision=Decision.INSUFFICIENT_INFORMATION, confidence=0,
            explanation="The expense assessment is temporarily unavailable.",
            next_action="RETRY_LATER",
        )

    async def _assess(self, expense) -> ExpenseAssessmentResponse:
        state = await self._invoke_graph({
                "expense_id": str(expense.id), "thread_id": expense.thread_id,
                "request_id": expense.request_id,
                "expense": ExpenseCreate.model_validate(_payload(expense)).model_dump(mode="json"),
                "assessment_date": self.dependencies.today().isoformat(),
                "hits": [], "rules": None, "citations": [],
            }, expense.thread_id)
        if state["missing_fields"]:
            return self._response(expense)
        response = ExpenseAssessmentResponse(
            expense_id=expense.id, thread_id=expense.thread_id, request_id=expense.request_id,
            citations=[PolicyCitation.model_validate(item) for item in state["citations"]],
            **state["decision"],
        )
        self.repository.save_assessment(response, state.get("rules") or {},
                                        state.get("model_name"), EXPENSE_RULE_PROMPT_VERSION)
        return response

    async def create(self, request: ExpenseCreate, request_id: str,
                     idempotency_key: str | None) -> ExpenseAssessmentResponse:
        expense, created = self.repository.create_or_get(request, request_id, idempotency_key)
        if not created:
            if expense.status != "ASSESSMENT_FAILED" or not self.repository.retry_failed(expense.id):
                return self._response(expense)
        try:
            return await self._assess(expense)
        except Exception:
            self.repository.mark_failed(expense.id)
            raise

    async def clarify(self, expense_id: UUID,
                      request: ExpenseClarification) -> ExpenseAssessmentResponse | None:
        updates = request.model_dump(exclude_unset=True, exclude_none=True)
        if not updates:
            raise ValueError("clarification must provide a value")
        expense = self.repository.clarify(expense_id, updates)
        if expense is None:
            return None
        if expense.status == "PENDING_CLARIFICATION":
            await self._invoke_graph({
                    "expense": ExpenseCreate.model_validate(_payload(expense)).model_dump(mode="json"),
                }, expense.thread_id)
            return self._response(expense)
        try:
            return await self._assess(expense)
        except Exception:
            self.repository.mark_failed(expense.id)
            raise
