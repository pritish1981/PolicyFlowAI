"""Validate evidence references against authoritative active policy records."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.policy_document import PolicyDocument
from app.models.policy_chunk import PolicyChunk
from app.rag.retrieval.rrf import SearchHit
from app.core.config import settings


@dataclass(frozen=True)
class Citation:
    chunk_id: UUID
    policy_code: str
    version: str
    section_id: str
    section_title: str
    excerpt: str
    score: float


def validate_citations(
    hits: list[SearchHit], session: Session, as_of: date,
    retrieved_ids: set[UUID] | None = None,
    cited_ids: set[UUID] | None = None,
    diagnostics: dict[str, int] | None = None,
) -> list[Citation]:
    """Reject any citation whose claimed identity or eligibility differs from storage."""
    allowed = retrieved_ids if retrieved_ids is not None else {hit.chunk_id for hit in hits}
    requested = cited_ids if cited_ids is not None else {hit.chunk_id for hit in hits}
    if diagnostics is not None:
        diagnostics["not_retrieved"] = len(requested - allowed)
    selected = [hit for hit in hits if hit.chunk_id in allowed and hit.chunk_id in requested]
    if not selected:
        return []
    ids = [hit.chunk_id for hit in selected]
    rows = session.execute(
        select(PolicyChunk, PolicyDocument).join(PolicyDocument)
        .where(PolicyChunk.id.in_(ids), PolicyDocument.status == "ACTIVE",
               PolicyDocument.effective_date <= as_of,
               or_(PolicyDocument.expiry_date.is_(None), PolicyDocument.expiry_date > as_of))
    ).all()
    by_id = {chunk.id: (chunk, document) for chunk, document in rows}
    citations = []
    for hit in selected:
        pair = by_id.get(hit.chunk_id)
        if pair is None:
            if diagnostics is not None:
                diagnostics["inactive_or_out_of_effect"] = (
                    diagnostics.get("inactive_or_out_of_effect", 0) + 1)
            continue
        chunk, document = pair
        if (document.policy_code, document.version, chunk.section_id, chunk.section_title, chunk.content) != (
            hit.policy_code, hit.version, hit.section_id, hit.section_title, hit.content
        ):
            if diagnostics is not None:
                diagnostics["identity_mismatch"] = diagnostics.get("identity_mismatch", 0) + 1
            continue
        normalized = " ".join(chunk.content.split())
        limit = settings.citation_excerpt_chars
        excerpt = normalized if len(normalized) <= limit else normalized[:limit - 1].rstrip() + "…"
        citations.append(Citation(chunk.id, document.policy_code, document.version,
                                  chunk.section_id, chunk.section_title, excerpt, hit.score))
    return citations
