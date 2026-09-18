"""Credential-free Phase 003 Policy Q&A tests."""
import asyncio
import json
import logging
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes.policies import get_policy_service
from app.core.config import Settings, settings
from app.core.exceptions import (
    ModelUnavailableError,
    RerankerUnavailableError,
    RetrievalUnavailableError,
    StructuredOutputError,
)
from app.gateway.model_gateway import GatewayResult, ModelContext, ModelGateway, ModelUsage
from app.gateway.prompts import POLICY_QA_SYSTEM_PROMPT, build_policy_qa_messages
from app.gateway.providers.base import ProviderResult
from app.gateway.routing import ModelTask
from app.graph.graph import PolicyQADependencies
from app.main import app
from app.rag.citations.validator import validate_citations
from app.rag.reranking import rerank
from app.rag.retrieval.hybrid_retriever import (
    HybridResults,
    policy_qa_filters,
    retrieve,
    search,
)
from app.rag.retrieval.rrf import SearchHit, fuse
from app.schemas.policy import (
    EvidenceStatus, GroundedPolicyAnswer, PolicyAnswerResponse, PolicyQueryRequest,
)
from app.services.policy_service import PolicyService


def _hit(content: str = "The domestic hotel limit is INR 7,000 per night.") -> SearchHit:
    return SearchHit(uuid4(), "POL-002", "1.0", "domestic-hotel-limit",
                     "Domestic Hotel Limit", content)


class FakeGateway:
    def __init__(self, hit: SearchHit, insufficient: bool = False, fail: bool = False):
        self.hit, self.insufficient, self.fail, self.calls = hit, insufficient, fail, 0

    async def invoke_structured(self, **_kwargs):
        self.calls += 1
        if self.fail:
            raise ModelUnavailableError("offline")
        output = GroundedPolicyAnswer(
            answer="The standard domestic hotel reimbursement limit is INR 7,000 per night."
                   if not self.insufficient else "Not enough evidence.",
            citation_chunk_ids=[] if self.insufficient else [self.hit.chunk_id],
            insufficient_information=self.insufficient,
        )
        return GatewayResult(output, ModelUsage("fake", "fake-policy", 4, 10, 12, 0))


class FakeSession:
    def __init__(self, hit: SearchHit, rows: bool = True):
        self.hit, self.rows = hit, rows

    def __enter__(self): return self
    def __exit__(self, *_args): return None

    def execute(self, _statement):
        chunk = SimpleNamespace(id=self.hit.chunk_id, section_id=self.hit.section_id,
                                section_title=self.hit.section_title, content=self.hit.content)
        document = SimpleNamespace(policy_code=self.hit.policy_code, version=self.hit.version)
        return SimpleNamespace(all=lambda: [(chunk, document)] if self.rows else [])


def _service(hit: SearchHit, *, no_evidence: bool = False, invalid_citation: bool = False,
             gateway: FakeGateway | None = None) -> PolicyService:
    def retrieve_fake(_query, _factory, *, filters):
        assert filters.status == "ACTIVE"
        return HybridResults([], [] if no_evidence else [hit])

    gateway = gateway or FakeGateway(hit)
    return PolicyService(PolicyQADependencies(
        session_factory=lambda: FakeSession(hit, not invalid_citation),
        gateway=gateway, retriever=retrieve_fake, reranker=None,
        today=lambda: date(2026, 9, 16),
    ))


def test_request_and_structured_schemas_are_strict():
    assert PolicyQueryRequest(question="  hotel limit?  ").question == "hotel limit?"
    for value in (" ", "ab", "x" * 2001):
        with pytest.raises(ValidationError):
            PolicyQueryRequest(question=value)
    with pytest.raises(ValidationError):
        PolicyQueryRequest(question="hotel", unsupported=True)
    with pytest.raises(ValidationError):
        GroundedPolicyAnswer(answer="unknown", citation_chunk_ids=["not-a-uuid"])
    assert GroundedPolicyAnswer(answer="unknown", insufficient_information=True).insufficient_information
    with pytest.raises(ValidationError):
        PolicyAnswerResponse(request_id="r", answer="fact", citations=[],
                             evidence_status=EvidenceStatus.GROUNDED)


def test_configuration_defaults_are_safe():
    configured = Settings(_env_file=None, database_url="postgresql+psycopg://x:x@localhost/x",
                          redis_url="redis://localhost:6379/0")
    assert configured.retrieval_top_n == 20
    assert configured.rrf_k == 60
    assert 3 <= configured.rerank_top_k <= 5
    assert configured.citation_required is True
    assert configured.openai_api_key is None


def test_metadata_filters_are_deterministic():
    filters = policy_qa_filters("hotel", "india", date(2026, 9, 16))
    assert filters.telemetry() == {"status": "ACTIVE", "as_of": "2026-09-16",
                                   "category": "HOTEL", "region": "INDIA"}
    assert policy_qa_filters(None, None, date(2026, 9, 16)).telemetry() == {
        "status": "ACTIVE", "as_of": "2026-09-16"}


def test_retrieval_exposes_lexical_and_vector_stages_and_preserves_search(monkeypatch):
    lexical_hit, vector_hit = _hit("lexical"), _hit("vector")
    monkeypatch.setattr(
        "app.rag.retrieval.hybrid_retriever.embed_texts", lambda _queries: [[0.1, 0.2]]
    )
    monkeypatch.setattr(
        "app.rag.retrieval.hybrid_retriever.lexical_search",
        lambda _query, _eligibility, _factory, top_n: [lexical_hit] if top_n == 20 else [],
    )
    monkeypatch.setattr(
        "app.rag.retrieval.hybrid_retriever.vector_search",
        lambda _vector, _eligibility, _factory, top_n: [vector_hit] if top_n == 20 else [],
    )
    filters = policy_qa_filters("HOTEL", "INDIA", date(2026, 9, 16))
    stages = retrieve("hotel limit", Mock(), filters=filters)
    assert stages.lexical_hits == [lexical_hit]
    assert stages.vector_hits == [vector_hit]
    fused = search(
        "hotel limit", Mock(), domain="HOTEL", region="INDIA", as_of=date(2026, 9, 16)
    )
    assert {hit.chunk_id for hit in fused} == {lexical_hit.chunk_id, vector_hit.chunk_id}
    assert any(hit.lexical_rank == 1 for hit in fused)
    assert any(hit.vector_rank == 1 for hit in fused)


def test_rrf_preserves_ranks_and_deduplicates():
    common, lexical, vector = _hit("common"), _hit("lexical"), _hit("vector")
    result = fuse([[common, lexical, common], [vector, common]], k=60)
    assert len(result) == 3
    by_id = {item.chunk_id: item for item in result}
    assert by_id[common.chunk_id].lexical_rank == 1
    assert by_id[common.chunk_id].vector_rank == 2
    assert by_id[lexical.chunk_id].vector_rank is None
    assert by_id[vector.chunk_id].lexical_rank is None
    assert result[0].chunk_id == common.chunk_id
    assert result[0].rrf_score == pytest.approx(1 / 61 + 1 / 62)


def test_reranker_success_and_configured_fallback(monkeypatch):
    hit = _hit()
    fake = Mock()
    fake.rerank.return_value = [hit]
    assert rerank("hotel", [hit], fake) == [hit]
    fake.rerank.side_effect = RuntimeError("offline")
    monkeypatch.setattr(settings, "rerank_fallback_to_rrf", True)
    assert rerank("hotel", [hit], fake) == [hit]
    monkeypatch.setattr(settings, "rerank_fallback_to_rrf", False)
    with pytest.raises(RerankerUnavailableError):
        rerank("hotel", [hit], fake)


def test_citation_validator_accepts_authoritative_and_rejects_mismatch(monkeypatch):
    hit = _hit("x" * 100)
    monkeypatch.setattr(settings, "citation_excerpt_chars", 30)
    valid = validate_citations([hit], FakeSession(hit), date(2026, 9, 16),
                               {hit.chunk_id}, {hit.chunk_id})
    assert len(valid) == 1 and len(valid[0].excerpt) <= 30
    assert validate_citations([hit], FakeSession(hit), date(2026, 9, 16),
                              {hit.chunk_id}, set()) == []
    mismatch = SearchHit(hit.chunk_id, "POL-999", hit.version, hit.section_id,
                         hit.section_title, hit.content)
    assert validate_citations([mismatch], FakeSession(hit), date(2026, 9, 16)) == []
    assert validate_citations([hit], FakeSession(hit, False), date(2026, 9, 16)) == []


def test_prompt_contains_grounding_rules_and_exact_evidence():
    hit = _hit()
    messages = build_policy_qa_messages("What is the limit?", [hit])
    assert "no external knowledge" in POLICY_QA_SYSTEM_PROMPT
    assert "Do not decide employee expense compliance" in POLICY_QA_SYSTEM_PROMPT
    assert "Do not approve or reject exceptions" in POLICY_QA_SYSTEM_PROMPT
    assert str(hit.chunk_id) in messages[1]["content"]
    assert hit.policy_code in messages[1]["content"]


def test_gateway_validates_and_retries(monkeypatch):
    class Provider:
        def __init__(self): self.calls = 0
        async def generate_structured(self, **_kwargs):
            self.calls += 1
            if self.calls == 1: raise TimeoutError()
            return ProviderResult({"answer": "supported", "citation_chunk_ids": [],
                                   "insufficient_information": False}, "fake", "fake")
    provider = Provider()
    monkeypatch.setattr(settings, "model_max_retries", 1)
    result = asyncio.run(ModelGateway(provider).invoke_structured(
        task=ModelTask.POLICY_QA, messages=[{"role": "user", "content": "question"}],
        output_schema=GroundedPolicyAnswer, context=ModelContext("r")))
    assert result.output.answer == "supported" and provider.calls == 2


def test_gateway_rejects_invalid_structured_output_and_unavailable_provider(monkeypatch):
    class InvalidProvider:
        def __init__(self): self.calls = 0
        async def generate_structured(self, **_kwargs):
            self.calls += 1
            return ProviderResult({"answer": "missing required shape", "unexpected": True},
                                  "fake", "fake")

    invalid = InvalidProvider()
    monkeypatch.setattr(settings, "model_max_retries", 1)
    with pytest.raises(StructuredOutputError):
        asyncio.run(ModelGateway(invalid).invoke_structured(
            task=ModelTask.POLICY_QA, messages=[{"role": "user", "content": "question"}],
            output_schema=GroundedPolicyAnswer, context=ModelContext("r")))
    assert invalid.calls == 2

    class UnavailableProvider:
        def __init__(self): self.calls = 0
        async def generate_structured(self, **_kwargs):
            self.calls += 1
            raise ConnectionError("offline")

    unavailable = UnavailableProvider()
    with pytest.raises(ModelUnavailableError):
        asyncio.run(ModelGateway(unavailable).invoke_structured(
            task=ModelTask.POLICY_QA, messages=[{"role": "user", "content": "question"}],
            output_schema=GroundedPolicyAnswer, context=ModelContext("r")))
    assert unavailable.calls == 2


def test_service_grounded_abstention_and_no_model_for_no_hits():
    hit = _hit()
    grounded = asyncio.run(_service(hit).query(PolicyQueryRequest(
        question="What is the hotel limit?", category="HOTEL", region="INDIA"), "req-1"))
    assert grounded.evidence_status == EvidenceStatus.GROUNDED
    assert grounded.citations[0].policy_code == "POL-002"
    no_hits_gateway = FakeGateway(hit)
    abstained = asyncio.run(_service(hit, no_evidence=True, gateway=no_hits_gateway).query(
        PolicyQueryRequest(question="unknown policy question"), "req-2"))
    assert abstained.evidence_status == EvidenceStatus.INSUFFICIENT_INFORMATION
    assert abstained.citations == [] and no_hits_gateway.calls == 0
    invalid = asyncio.run(_service(hit, invalid_citation=True).query(
        PolicyQueryRequest(question="What is the hotel limit?"), "req-3"))
    assert invalid.evidence_status == EvidenceStatus.INSUFFICIENT_INFORMATION


def test_service_propagates_gateway_failure():
    hit = _hit()
    with pytest.raises(ModelUnavailableError):
        asyncio.run(_service(hit, gateway=FakeGateway(hit, fail=True)).query(
            PolicyQueryRequest(question="What is the hotel limit?"), "req"))


def test_service_propagates_retrieval_failure():
    hit = _hit()

    def failed_retrieval(*_args, **_kwargs):
        raise RetrievalUnavailableError("database offline")

    service = PolicyService(PolicyQADependencies(
        session_factory=lambda: FakeSession(hit), gateway=FakeGateway(hit),
        retriever=failed_retrieval, reranker=None, today=lambda: date(2026, 9, 16),
    ))
    with pytest.raises(RetrievalUnavailableError):
        asyncio.run(service.query(PolicyQueryRequest(question="What is the hotel limit?"), "req"))


def test_graph_executes_the_phase_003_node_order_without_live_credentials():
    hit = _hit()
    service = _service(hit)

    async def collect_nodes():
        nodes = []
        async for update in service.graph.astream({
            "request_id": "graph-1",
            "thread_id": "graph-1",
            "scenario": "policy_qa",
            "user_query": "What is the hotel limit?",
            "assessment_date": date(2026, 9, 16),
            "errors": [],
        }, stream_mode="updates"):
            nodes.extend(update)
        return nodes

    assert asyncio.run(collect_nodes()) == [
        "validate_request",
        "set_policy_qa",
        "build_metadata_filters",
        "hybrid_retrieve",
        "fuse_results",
        "rerank_results",
        "generate_grounded_answer",
        "validate_citations",
        "final_response",
    ]


def test_api_grounded_abstention_validation_and_503():
    hit = _hit()
    client = TestClient(app)
    app.dependency_overrides[get_policy_service] = lambda: _service(hit)
    response = client.post("/api/v1/policy/query", headers={"X-Request-ID": "trace-1"},
                           json={"question": "What is the hotel limit?", "category": "HOTEL"})
    assert response.status_code == 200
    assert response.json()["request_id"] == "trace-1"
    assert response.json()["citations"][0]["policy_code"] == "POL-002"
    app.dependency_overrides[get_policy_service] = lambda: _service(hit, no_evidence=True)
    assert client.post("/api/v1/policy/query", json={"question": "unknown"}).json()[
        "evidence_status"] == "INSUFFICIENT_INFORMATION"
    assert client.post("/api/v1/policy/query", json={"question": "x"}).status_code == 422
    assert client.post("/api/v1/policy/query", json={"question": "valid", "extra": 1}).status_code == 422
    app.dependency_overrides[get_policy_service] = lambda: _service(
        hit, gateway=FakeGateway(hit, fail=True))
    assert client.post("/api/v1/policy/query", json={"question": "hotel limit"}).status_code == 503
    app.dependency_overrides.clear()


def test_api_missing_model_key_returns_controlled_503(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)
    get_policy_service.cache_clear()
    try:
        response = TestClient(app).post(
            "/api/v1/policy/query",
            headers={"X-Request-ID": "missing-key-1"},
            json={"question": "What is the hotel limit?"},
        )
        assert response.status_code == 503
        assert response.json()["detail"] == {
            "code": "MODEL_TEMPORARILY_UNAVAILABLE",
            "message": "Policy Q&A is temporarily unavailable.",
            "request_id": "missing-key-1",
            "retryable": True,
        }
    finally:
        get_policy_service.cache_clear()


def test_openapi_has_one_policy_query_operation():
    paths = app.openapi()["paths"]
    assert list(paths["/api/v1/policy/query"]) == ["post"]


def test_structured_logs_are_sanitized(caplog):
    hit = _hit("SECRET_DOCUMENT_BODY")
    with caplog.at_level(logging.INFO, logger="app.graph.graph"):
        asyncio.run(_service(hit).query(PolicyQueryRequest(question="hotel limit"), "log-1"))
    records = [getattr(record, "policyflow", {}) for record in caplog.records]
    assert any(item.get("request_id") == "log-1" for item in records)
    serialized = json.dumps(records)
    assert "SECRET_DOCUMENT_BODY" not in serialized
    assert "OPENAI_API_KEY" not in serialized


def test_golden_dataset_shape_and_unique_ids():
    path = Path(__file__).resolve().parents[2] / "evaluation" / "datasets" / "policy_qa_golden.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert 8 <= len(data) <= 12
    assert len({item["id"] for item in data}) == len(data)
    assert {"POL-002", "POL-003", "POL-004", "POL-005", "POL-006"} <= {
        item.get("expected_policy_code") for item in data}
