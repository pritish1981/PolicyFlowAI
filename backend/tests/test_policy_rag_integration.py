"""Live PostgreSQL migration, index, hybrid search and citation checks."""
from datetime import date
from pathlib import Path
import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.rag.retrieval.hybrid_retriever import search
from app.rag.citations.validator import validate_citations

_root = Path(__file__).resolve().parents[2]
_database_url = dotenv_values(_root / ".env").get("DATABASE_URL")
if not _database_url:
    pytest.skip("Live integration tests require DATABASE_URL in project .env", allow_module_level=True)
engine = create_engine(_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def test_policy_migration_indexes():
    with engine.connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "20260917_0003"
        rows = connection.execute(text(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'rag' "
            "AND tablename IN ('policy_document', 'policy_chunk')"
        )).scalars().all()
        names = set(rows)
        assert {"ix_policy_chunk_fts", "ix_policy_chunk_vector",
                "ix_policy_chunk_metadata", "ix_policy_document_status_domain"} <= names
        assert connection.scalar(text("SELECT extname FROM pg_extension WHERE extname='vector'")) == "vector"


def test_hybrid_search_and_verified_citations():
    with engine.connect() as connection:
        count = connection.scalar(text("SELECT count(*) FROM rag.policy_document"))
        assert count == 6
    hits = search("domestic hotel INR 7000 per night", SessionLocal,
                  domain="HOTEL", region="INDIA", travel_type="DOMESTIC",
                  as_of=date(2026, 9, 13))
    assert hits
    assert all(hit.policy_code == "POL-002" for hit in hits)
    assert all("international-hotel-limit" != hit.section_id for hit in hits)
    with SessionLocal() as session:
        citations = validate_citations(hits[:5], session, date(2026, 9, 13))
    assert citations
    assert all(citation.policy_code == "POL-002" for citation in citations)


def test_effective_date_filter_excludes_future_policy():
    assert search("hotel INR 7000", SessionLocal, domain="HOTEL",
                  as_of=date(2025, 1, 1)) == []
