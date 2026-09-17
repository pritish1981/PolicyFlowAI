"""Unit checks for section preservation, fusion and citation rejection."""
from datetime import date
from uuid import uuid4
from unittest.mock import Mock
import tiktoken

from app.rag.ingestion.chunker import chunk_markdown
from app.rag.retrieval.rrf import SearchHit, fuse
from app.rag.citations.validator import validate_citations


def test_chunker_preserves_section_boundary_and_overlap():
    body = "## Alpha\n" + " ".join(f"a{i}" for i in range(800))
    body += "\n## Beta\n" + " ".join(f"b{i}" for i in range(40))
    chunks = chunk_markdown(body, target=400, overlap=50)
    assert chunks[-1].section_id == "beta"
    assert all(chunk.section_id == "alpha" for chunk in chunks[:-1])
    encoding = tiktoken.get_encoding("cl100k_base")
    assert encoding.encode(chunks[0].content)[-50:] == encoding.encode(chunks[1].content)[:50]
    assert all("b0" not in chunk.content for chunk in chunks[:-1])


def test_rrf_deduplicates_and_adds_rank_scores():
    a = SearchHit(uuid4(), "POL-001", "1.0", "a", "A", "text")
    b = SearchHit(uuid4(), "POL-002", "1.0", "b", "B", "text")
    result = fuse([[a, b], [b, a]], k=60)
    assert len(result) == 2
    assert abs(result[0].score - (1 / 61 + 1 / 62)) < 1e-9


def test_citation_validator_rejects_unretrieved_chunk():
    hit = SearchHit(uuid4(), "POL-001", "1.0", "a", "A", "text")
    session = Mock()
    session.execute.return_value.all.return_value = []
    assert validate_citations([hit], session, date(2026, 1, 2)) == []


def test_citation_validator_rejects_reranker_added_chunk():
    hit = SearchHit(uuid4(), "POL-001", "1.0", "a", "A", "text")
    session = Mock()
    chunk = Mock(id=hit.chunk_id, section_id="a", section_title="A", content="text")
    document = Mock(policy_code="POL-001", version="1.0")
    session.execute.return_value.all.return_value = [(chunk, document)]
    assert len(validate_citations([hit], session, date(2026, 1, 2), {hit.chunk_id})) == 1
    assert validate_citations([hit], session, date(2026, 1, 2), set()) == []
