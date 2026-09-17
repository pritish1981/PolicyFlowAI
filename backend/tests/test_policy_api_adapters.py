"""API authorization and reranker adapter contracts."""
import asyncio
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.gateway.providers.openai_provider import OpenAIProvider
from app.rag.retrieval.rrf import SearchHit
from app.rag.reranking.cohere_reranker import CohereReranker
from app.rag.reranking.bge_reranker import BGEReranker
from app.schemas.policy import GroundedPolicyAnswer


def _hit() -> SearchHit:
    return SearchHit(uuid4(), "POL-002", "1.0", "domestic", "Domestic", "INR 7000")


def test_ingestion_api_requires_token(monkeypatch):
    monkeypatch.setattr(settings, "policy_admin_token", "test-secret")
    client = TestClient(app)
    assert client.post("/api/v1/admin/policies/ingest").status_code == 403
    assert client.post("/api/v1/admin/policies/ingest",
                       headers={"X-Policy-Admin-Token": "wrong"}).status_code == 403


def test_cohere_adapter_maps_only_returned_indices(monkeypatch):
    import cohere
    fake = Mock()
    fake.rerank.return_value.results = [Mock(index=0, relevance_score=0.9)]
    monkeypatch.setattr(cohere, "ClientV2", lambda **kwargs: fake)
    hit = _hit()
    output = CohereReranker("key", "model").rerank("hotel", [hit], 3)
    assert output[0].chunk_id == hit.chunk_id
    assert output[0].score == 0.9
    fake.rerank.assert_called_once()


def test_bge_adapter_orders_scores(monkeypatch):
    import fastembed.rerank.cross_encoder.text_cross_encoder as cross_encoder
    fake = Mock()
    fake.rerank.return_value = iter([0.1, 0.8])
    monkeypatch.setattr(cross_encoder, "TextCrossEncoder", lambda **kwargs: fake)
    first, second = _hit(), _hit()
    result = BGEReranker("model").rerank("hotel", [first, second], 1)
    assert [hit.chunk_id for hit in result] == [second.chunk_id]


def test_openai_adapter_uses_lazy_structured_responses_api(monkeypatch):
    expected = GroundedPolicyAnswer(
        answer="The limit is INR 7,000 per night.",
        citation_chunk_ids=[uuid4()],
    )
    parse = Mock()

    async def parse_async(**kwargs):
        parse(**kwargs)
        return SimpleNamespace(
            output_parsed=expected,
            usage=SimpleNamespace(input_tokens=12, output_tokens=9),
        )

    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=parse_async))
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **_kwargs: fake_client)
    result = asyncio.run(OpenAIProvider("test-key", 5.0).generate_structured(
        messages=[{"role": "user", "content": "question"}],
        output_schema=GroundedPolicyAnswer,
        model="test-model",
        max_output_tokens=200,
    ))
    assert result.output == expected
    assert result.provider == "openai"
    assert result.input_tokens == 12 and result.output_tokens == 9
    assert parse.call_args.kwargs["text_format"] is GroundedPolicyAnswer
    assert parse.call_args.kwargs["max_output_tokens"] == 200
