"""PostgreSQL FTS and pgvector retrieval with deterministic eligibility."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from typing import Callable

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import RetrievalUnavailableError
from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.rag.embeddings.embedding_provider import embed_texts
from app.rag.retrieval.lexical_retriever import lexical_search
from app.rag.retrieval.rrf import SearchHit, fuse
from app.rag.retrieval.vector_retriever import vector_search


@dataclass(frozen=True)
class MetadataFilters:
    status: str
    as_of: date
    category: str | None = None
    region: str | None = None

    def telemetry(self) -> dict[str, str]:
        values = {"status": self.status, "as_of": self.as_of.isoformat()}
        if self.category:
            values["category"] = self.category
        if self.region:
            values["region"] = self.region
        return values


@dataclass(frozen=True)
class HybridResults:
    lexical_hits: list[SearchHit]
    vector_hits: list[SearchHit]


def policy_qa_filters(category: str | None, region: str | None, as_of: date) -> MetadataFilters:
    return MetadataFilters(
        status="ACTIVE", as_of=as_of,
        category=category.upper() if category else None,
        region=region.upper() if region else None,
    )


def build_filters(domain: str | None, region: str | None, travel_type: str | None,
                  version: str | None, as_of: date):
    terms = [
        PolicyDocument.status == "ACTIVE",
        PolicyDocument.embedding_model == settings.embedding_model,
        PolicyDocument.effective_date <= as_of,
        or_(PolicyDocument.expiry_date.is_(None), PolicyDocument.expiry_date > as_of),
    ]
    if domain:
        terms.append(PolicyDocument.domain == domain)
    if version:
        terms.append(PolicyDocument.version == version)
    if region:
        terms.append(PolicyDocument.region.in_(["GLOBAL", region]))
    if travel_type:
        terms.append(PolicyDocument.travel_type.in_(["ALL", travel_type]))
        terms.append(PolicyChunk.metadata_["travel_type"].astext.in_(["ALL", travel_type]))
    return and_(*terms)


def retrieve(query: str, session_factory: Callable[[], Session], *,
             filters: MetadataFilters, travel_type: str | None = None,
             version: str | None = None) -> HybridResults:
    if not query.strip():
        raise ValueError("query cannot be empty")
    try:
        vector = embed_texts([query])[0]
        eligibility = build_filters(filters.category, filters.region, travel_type,
                                    version, filters.as_of)
        with ThreadPoolExecutor(max_workers=2) as executor:
            lexical = executor.submit(lexical_search, query, eligibility, session_factory,
                                      settings.retrieval_top_n)
            semantic = executor.submit(vector_search, vector, eligibility, session_factory,
                                       settings.retrieval_top_n)
            return HybridResults(lexical.result(), semantic.result())
    except ValueError:
        raise
    except Exception as exc:
        raise RetrievalUnavailableError("policy retrieval failed") from exc


def search(query: str, session_factory: Callable[[], Session], *,
           domain: str | None = None, region: str | None = None,
           travel_type: str | None = None, version: str | None = None,
           as_of: date | None = None) -> list[SearchHit]:
    current_date = as_of or date.today()
    results = retrieve(query, session_factory,
                       filters=policy_qa_filters(domain, region, current_date),
                       travel_type=travel_type, version=version)
    return fuse([results.lexical_hits, results.vector_hits], settings.rrf_k,
                settings.retrieval_top_n)
