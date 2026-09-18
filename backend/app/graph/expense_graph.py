"""Expense path: compact checkpoint state, verified evidence, deterministic decision."""
from dataclasses import dataclass
from datetime import date
import logging
from typing import Callable
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.gateway.model_gateway import ModelContext, ModelGateway
from app.gateway.prompts import EXPENSE_RULE_PROMPT_VERSION, build_expense_rule_messages
from app.gateway.routing import ModelTask
from app.graph.state import ExpenseState
from app.rag.retrieval.rrf import SearchHit
from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.rules.expense_rules import evaluate_expense_rules
from app.schemas.expense import ExpenseCreate, PolicyRuleSet
from app.services.expense_evidence import gather_expense_evidence
from app.services.expense_rule_validation import validated_rules

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExpenseDependencies:
    session_factory: Callable
    gateway: ModelGateway
    retriever: Callable | None = None
    reranker: object | None = None
    today: Callable[[], date] = date.today


def build_expense_graph(deps: ExpenseDependencies, checkpointer=None):
    def load_hits(ids: list[str]) -> list[SearchHit]:
        if not ids:
            return []
        with deps.session_factory() as session:
            rows = session.execute(select(PolicyChunk, PolicyDocument).join(PolicyDocument)
                                   .where(PolicyChunk.id.in_([UUID(item) for item in ids]))).all()
        by_id = {str(chunk.id): SearchHit(chunk.id, document.policy_code,
                  document.version, chunk.section_id, chunk.section_title, chunk.content)
                 for chunk, document in rows}
        return [by_id[item] for item in ids if item in by_id]

    def validate_intake(state: ExpenseState) -> dict:
        expense = ExpenseCreate.model_validate(state["expense"])
        return {"missing_fields": expense.missing_fields(), "scenario": "expense_assessment"}

    def route(state: ExpenseState) -> str:
        return "missing" if state["missing_fields"] else "ready"

    def retrieve_evidence(state: ExpenseState) -> dict:
        expense = ExpenseCreate.model_validate(state["expense"])
        kwargs = {"assessment_date": date.fromisoformat(state["assessment_date"]),
                  "reranker": deps.reranker}
        if deps.retriever is not None:
            kwargs["retriever"] = deps.retriever
        evidence = gather_expense_evidence(expense, deps.session_factory, **kwargs)
        logger.info("expense.evidence_retrieved", extra={"policyflow": {
            "request_id": state["request_id"], "thread_id": state["thread_id"],
            "expense_id": state["expense_id"], "category_counts": evidence.category_counts,
            "selected_chunk_ids": [str(hit.chunk_id) for hit in evidence.reranked_hits]}})
        return {"hits": [str(hit.chunk_id) for hit in evidence.reranked_hits]}

    async def extract_rules(state: ExpenseState) -> dict:
        hits = load_hits(state["hits"])
        if not hits:
            return {"rules": None, "model_name": None}
        result = await deps.gateway.invoke_structured(
            task=ModelTask.EXPENSE_POLICY_RULE,
            messages=build_expense_rule_messages(state["expense"], hits),
            output_schema=PolicyRuleSet,
            context=ModelContext(request_id=state["request_id"],
                                 thread_id=state["thread_id"],
                                 prompt_version=EXPENSE_RULE_PROMPT_VERSION),
        )
        logger.info("expense.rules_extracted", extra={"policyflow": {
            "request_id": state["request_id"], "model": result.usage.model,
            "rule_types": [rule.rule_type.value for rule in result.output.rules],
            "latency_ms": result.usage.latency_ms}})
        return {"rules": result.output.model_dump(mode="json"),
                "model_name": result.usage.model}

    def verify_sources(state: ExpenseState) -> dict:
        rules = PolicyRuleSet.model_validate(state["rules"]) if state.get("rules") else None
        if rules is None:
            return {"rules": None, "citations": []}
        verified, citations = validated_rules(
            rules, load_hits(state["hits"]), deps.session_factory,
            date.fromisoformat(state["assessment_date"]),
            expense_type=ExpenseCreate.model_validate(state["expense"]).expense_type,
            travel_type=state["expense"].get("travel_type"),
        )
        return {"rules": verified.model_dump(mode="json") if verified else None,
                "citations": [{"chunk_id": str(item.chunk_id),
                               "policy_code": item.policy_code, "policy_version": item.version,
                               "section_id": item.section_id, "section_title": item.section_title,
                               "excerpt": item.excerpt} for item in citations]}

    def decide(state: ExpenseState) -> dict:
        rules = PolicyRuleSet.model_validate(state["rules"]) if state.get("rules") else None
        assessment = evaluate_expense_rules(
            ExpenseCreate.model_validate(state["expense"]), rules,
            {UUID(item["chunk_id"]) for item in state.get("citations", [])},
        )
        logger.info("expense.assessed", extra={"policyflow": {
            "request_id": state["request_id"], "expense_id": state["expense_id"],
            "decision": assessment.decision.value, "confidence": str(assessment.confidence),
            "citation_count": len(state.get("citations", []))}})
        return {"decision": {
            "decision": assessment.decision.value,
            "policy_limit": str(assessment.policy_limit) if assessment.policy_limit is not None else None,
            "confidence": str(assessment.confidence),
            "explanation": assessment.explanation, "next_action": assessment.next_action,
        }}

    graph = StateGraph(ExpenseState)
    graph.add_node("validate_intake", validate_intake)
    graph.add_node("retrieve_evidence", retrieve_evidence)
    graph.add_node("extract_rules", extract_rules)
    graph.add_node("verify_sources", verify_sources)
    graph.add_node("decide", decide)
    graph.add_edge(START, "validate_intake")
    graph.add_conditional_edges("validate_intake", route,
                                {"missing": END, "ready": "retrieve_evidence"})
    graph.add_edge("retrieve_evidence", "extract_rules")
    graph.add_edge("extract_rules", "verify_sources")
    graph.add_edge("verify_sources", "decide")
    graph.add_edge("decide", END)
    return graph.compile(checkpointer=checkpointer)
