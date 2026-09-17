"""PostgreSQL full-text policy candidate retrieval."""
from typing import Callable
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.rag.retrieval.rrf import SearchHit


def lexical_search(query: str, eligibility, session_factory: Callable[[], Session], limit: int) -> list[SearchHit]:
    """Return ranked FTS matches after deterministic SQL eligibility filters."""
    tsquery = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank_cd(PolicyChunk.search_vector, tsquery)
    statement = (
        select(PolicyChunk.id, PolicyDocument.policy_code, PolicyDocument.version,
               PolicyChunk.section_id, PolicyChunk.section_title, PolicyChunk.content,
               rank.label("rank"))
        .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        .where(eligibility, PolicyChunk.search_vector.op("@@")(tsquery))
        .order_by(rank.desc(), PolicyChunk.id).limit(limit)
    )
    with session_factory() as session:
        return [SearchHit(row.id, row.policy_code, row.version, row.section_id,
                          row.section_title, row.content, float(row.rank))
                for row in session.execute(statement).all()]
