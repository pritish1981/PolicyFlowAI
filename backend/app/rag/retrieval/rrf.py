"""Reciprocal rank fusion over chunk identifiers."""
from dataclasses import dataclass, replace
from uuid import UUID


@dataclass(frozen=True)
class SearchHit:
    chunk_id: UUID
    policy_code: str
    version: str
    section_id: str
    section_title: str
    content: str
    score: float = 0.0
    lexical_rank: int | None = None
    vector_rank: int | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None


def fuse(lists: list[list[SearchHit]], k: int = 60, limit: int = 20) -> list[SearchHit]:
    """Fuse rank lists, deduplicating by chunk ID."""
    if k <= 0:
        raise ValueError("k must be positive")
    scores: dict[UUID, float] = {}
    hits: dict[UUID, SearchHit] = {}
    ranks: dict[UUID, list[int | None]] = {}
    for list_index, items in enumerate(lists):
        seen: set[UUID] = set()
        for rank, hit in enumerate(items, start=1):
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank)
            hits.setdefault(hit.chunk_id, hit)
            ranks.setdefault(hit.chunk_id, [None, None])
            if list_index < 2:
                ranks[hit.chunk_id][list_index] = rank
    ordered = sorted(scores, key=lambda key: (-scores[key], str(key)))
    return [replace(hits[key], score=scores[key], rrf_score=scores[key],
                    lexical_rank=ranks[key][0], vector_rank=ranks[key][1])
            for key in ordered[:limit]]
