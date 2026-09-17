"""Reranking adapter protocol."""
from typing import Protocol
from app.rag.retrieval.rrf import SearchHit


class Reranker(Protocol):
    def rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        """Return a subset of input hits in relevance order."""
        ...
