"""Policy Q&A application service."""
from datetime import date
from uuid import uuid4

from app.graph.graph import PolicyQADependencies, build_policy_qa_graph
from app.schemas.policy import (
    EvidenceStatus, PolicyAnswerResponse, PolicyCitation, PolicyQueryRequest,
    SAFE_ABSTENTION,
)
from app.observability.context import TraceContext
from app.observability.tracing import stage_span


class PolicyService:
    def __init__(self, dependencies: PolicyQADependencies) -> None:
        self.dependencies = dependencies
        self.graph = build_policy_qa_graph(dependencies)

    async def query(self, request: PolicyQueryRequest, request_id: str | None = None,
                    thread_id: str | None = None) -> PolicyAnswerResponse:
        correlation_id = request_id or str(uuid4())
        correlated_thread = thread_id or correlation_id
        with stage_span("policy_qa.request",
                        TraceContext(correlation_id, correlated_thread, "policy_qa")):
            state = await self.graph.ainvoke({
                "request_id": correlation_id, "thread_id": correlated_thread,
                "scenario": "policy_qa", "user_query": request.question,
                "category": request.category, "region": request.region,
                "assessment_date": self.dependencies.today(), "errors": [],
            })
        citations = [PolicyCitation(
            chunk_id=item.chunk_id, policy_code=item.policy_code,
            policy_version=item.version, section_id=item.section_id,
            section_title=item.section_title, excerpt=item.excerpt,
        ) for item in state.get("citations", [])]
        status = EvidenceStatus(state.get(
            "evidence_status", EvidenceStatus.INSUFFICIENT_INFORMATION.value))
        if status == EvidenceStatus.GROUNDED and not citations:
            status = EvidenceStatus.INSUFFICIENT_INFORMATION
        return PolicyAnswerResponse(
            request_id=correlation_id,
            answer=state.get("answer", SAFE_ABSTENTION) if citations else SAFE_ABSTENTION,
            citations=citations if status == EvidenceStatus.GROUNDED else [],
            evidence_status=status,
        )
