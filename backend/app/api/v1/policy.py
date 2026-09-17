"""Evidence-only policy query API."""
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.session import SessionLocal
from app.rag.citations.validator import Citation, validate_citations
from app.rag.reranking import rerank
from app.rag.retrieval.hybrid_retriever import search

router = APIRouter(prefix="/api/v1/policy", tags=["policy"])


class PolicyQuery(BaseModel):
    query: str = Field(min_length=1)
    domain: str | None = None
    region: str | None = None
    travel_type: str | None = None
    version: str | None = None
    as_of: date | None = None


class PolicyQueryResponse(BaseModel):
    status: str
    citations: list[Citation]


@router.post("/query", response_model=PolicyQueryResponse)
def query_policy(request: PolicyQuery) -> PolicyQueryResponse:
    """Find and validate policy evidence without generating an answer."""
    as_of = request.as_of or date.today()
    try:
        hits = search(request.query, SessionLocal, domain=request.domain,
                      region=request.region, travel_type=request.travel_type,
                      version=request.version, as_of=as_of)
        final_hits = rerank(request.query, hits)
        with SessionLocal() as session:
            citations = validate_citations(
                final_hits, session, as_of, {hit.chunk_id for hit in hits}
            )
        return PolicyQueryResponse(status="evidence_found" if citations else "abstain", citations=citations)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
