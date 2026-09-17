"""PostgreSQL pgvector cosine policy candidate retrieval."""
from typing import Callable, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.rag.retrieval.rrf import SearchHit


def vector_search(vector: Sequence[float], eligibility, session_factory: Callable[[], Session], limit: int) -> list[SearchHit]:
    """Return nearest vectors after deterministic SQL eligibility filters."""
    distance = PolicyChunk.embedding.cosine_distance(list(vector))
    statement = (
        select(PolicyChunk.id, PolicyDocument.policy_code, PolicyDocument.version,
               PolicyChunk.section_id, PolicyChunk.section_title, PolicyChunk.content,
               (1 - distance).label("rank"))
        .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        .where(eligibility).order_by(distance, PolicyChunk.id).limit(limit)
    )
    with session_factory() as session:
        return [SearchHit(row.id, row.policy_code, row.version, row.section_id,
                          row.section_title, row.content, float(row.rank))
                for row in session.execute(statement).all()]
