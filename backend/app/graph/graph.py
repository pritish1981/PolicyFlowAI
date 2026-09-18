"""Phase 003 Policy Q&A LangGraph."""
import logging
from dataclasses import asdict, dataclass
from datetime import date
from typing import Callable

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.gateway.model_gateway import ModelContext, ModelGateway
from app.gateway.prompts import build_policy_qa_messages
from app.gateway.routing import ModelTask
from app.graph.state import PolicyQAState
from app.rag.citations.validator import validate_citations
from app.rag.reranking import rerank
from app.rag.retrieval.hybrid_retriever import (
    HybridResults, policy_qa_filters, retrieve,
)
from app.rag.retrieval.rrf import SearchHit, fuse
from app.schemas.policy import EvidenceStatus, GroundedPolicyAnswer, SAFE_ABSTENTION
from app.graph.expense_graph import ExpenseDependencies, build_expense_graph

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyQADependencies:
    session_factory: Callable
    gateway: ModelGateway
    retriever: Callable = retrieve
    reranker: object | None = None
    today: Callable[[], date] = date.today


def _log(event: str, state: PolicyQAState, **fields) -> None:
    logger.info(event, extra={"policyflow": {
        "event": event, "request_id": state.get("request_id"),
        "scenario": "policy_qa", **fields,
    }})


def build_policy_qa_graph(deps: PolicyQADependencies):
    def validate_request(state: PolicyQAState) -> dict:
        query = state.get("user_query", "").strip()
        if not 3 <= len(query) <= 2000:
            raise ValueError("question must contain between 3 and 2000 characters")
        _log("policy_qa.request_validated", state)
        return {"user_query": query, "errors": []}

    def set_policy_qa(state: PolicyQAState) -> dict:
        return {"scenario": "policy_qa"}

    def build_metadata_filters(state: PolicyQAState) -> dict:
        filters = policy_qa_filters(state.get("category"), state.get("region"),
                                    state.get("assessment_date") or deps.today())
        _log("policy_qa.filters_built", state, metadata_filters=filters.telemetry())
        return {"metadata_filters": filters}

    def hybrid_retrieve(state: PolicyQAState) -> dict:
        results: HybridResults = deps.retriever(
            state["user_query"], deps.session_factory, filters=state["metadata_filters"],
        )
        _log("policy_qa.retrieved", state, lexical_count=len(results.lexical_hits),
             vector_count=len(results.vector_hits),
             retrieved_chunk_ids=[str(h.chunk_id) for h in results.lexical_hits + results.vector_hits])
        return {"lexical_hits": results.lexical_hits, "vector_hits": results.vector_hits}

    def fuse_results(state: PolicyQAState) -> dict:
        fused = fuse([state.get("lexical_hits", []), state.get("vector_hits", [])],
                     settings.rrf_k, settings.retrieval_top_n)
        _log("policy_qa.fused", state, fused_count=len(fused),
             rrf_scores={str(h.chunk_id): h.rrf_score for h in fused})
        return {"fused_hits": fused}

    def rerank_results(state: PolicyQAState) -> dict:
        fused = state.get("fused_hits", [])
        ranked = rerank(state["user_query"], fused, deps.reranker)
        fallback = bool(ranked and all(hit.rerank_score is None for hit in ranked))
        _log("policy_qa.reranked", state, reranked_count=len(ranked),
             rerank_fallback=fallback,
             rerank_scores={str(h.chunk_id): h.rerank_score for h in ranked})
        return {"reranked_hits": ranked, "rerank_fallback": fallback}

    async def generate_grounded_answer(state: PolicyQAState) -> dict:
        hits = state.get("reranked_hits", [])
        if not hits:
            return {"answer": SAFE_ABSTENTION, "citation_chunk_ids": [],
                    "evidence_status": EvidenceStatus.INSUFFICIENT_INFORMATION.value}
        result = await deps.gateway.invoke_structured(
            task=ModelTask.POLICY_QA,
            messages=build_policy_qa_messages(state["user_query"], hits),
            output_schema=GroundedPolicyAnswer,
            context=ModelContext(request_id=state["request_id"], thread_id=state.get("thread_id")),
        )
        output = result.output
        usage = asdict(result.usage)
        _log("policy_qa.generated", state, model=usage["model"], provider=usage["provider"],
             model_latency_ms=usage["latency_ms"], token_usage={
                 "input": usage["input_tokens"], "output": usage["output_tokens"]})
        if output.insufficient_information:
            return {"answer": SAFE_ABSTENTION, "citation_chunk_ids": [],
                    "evidence_status": EvidenceStatus.INSUFFICIENT_INFORMATION.value,
                    "model_usage": usage}
        return {"answer": output.answer, "citation_chunk_ids": output.citation_chunk_ids,
                "model_usage": usage}

    def validate_model_citations(state: PolicyQAState) -> dict:
        if state.get("evidence_status") == EvidenceStatus.INSUFFICIENT_INFORMATION.value:
            return {"citations": []}
        hits = state.get("reranked_hits", [])
        cited_ids = set(state.get("citation_chunk_ids", []))
        with deps.session_factory() as session:
            citations = validate_citations(
                hits, session, state["assessment_date"],
                retrieved_ids={hit.chunk_id for hit in hits}, cited_ids=cited_ids,
            )
        _log("policy_qa.citations_validated", state, citation_valid_count=len(citations))
        if settings.citation_required and not citations:
            return {"answer": SAFE_ABSTENTION, "citations": [],
                    "evidence_status": EvidenceStatus.INSUFFICIENT_INFORMATION.value}
        return {"citations": citations, "evidence_status": EvidenceStatus.GROUNDED.value}

    def final_response(state: PolicyQAState) -> dict:
        status = state.get("evidence_status", EvidenceStatus.INSUFFICIENT_INFORMATION.value)
        citations = state.get("citations", [])
        if status != EvidenceStatus.GROUNDED.value or not citations:
            status, citations, answer = (EvidenceStatus.INSUFFICIENT_INFORMATION.value,
                                         [], SAFE_ABSTENTION)
        else:
            answer = state.get("answer", SAFE_ABSTENTION)
        _log("policy_qa.completed", state, evidence_status=status,
             citation_valid_count=len(citations))
        return {"answer": answer, "citations": citations, "evidence_status": status}

    graph = StateGraph(PolicyQAState)
    graph.add_node("validate_request", validate_request)
    graph.add_node("set_policy_qa", set_policy_qa)
    graph.add_node("build_metadata_filters", build_metadata_filters)
    graph.add_node("hybrid_retrieve", hybrid_retrieve)
    graph.add_node("fuse_results", fuse_results)
    graph.add_node("rerank_results", rerank_results)
    graph.add_node("generate_grounded_answer", generate_grounded_answer)
    graph.add_node("validate_citations", validate_model_citations)
    graph.add_node("final_response", final_response)
    graph.add_edge(START, "validate_request")
    graph.add_edge("validate_request", "set_policy_qa")
    graph.add_edge("set_policy_qa", "build_metadata_filters")
    graph.add_edge("build_metadata_filters", "hybrid_retrieve")
    graph.add_edge("hybrid_retrieve", "fuse_results")
    graph.add_edge("fuse_results", "rerank_results")
    graph.add_edge("rerank_results", "generate_grounded_answer")
    graph.add_edge("generate_grounded_answer", "validate_citations")
    graph.add_edge("validate_citations", "final_response")
    graph.add_edge("final_response", END)
    return graph.compile()
