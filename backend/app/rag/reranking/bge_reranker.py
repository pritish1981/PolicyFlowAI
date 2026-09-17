"""Local BGE cross-encoder fallback adapter."""
from dataclasses import replace
from app.rag.retrieval.rrf import SearchHit


class BGEReranker:
    def __init__(self, model: str) -> None:
        self.model = model

    def rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        if not hits:
            return []
        from fastembed.rerank.cross_encoder.text_cross_encoder import TextCrossEncoder
        scores = list(TextCrossEncoder(model_name=self.model).rerank(query, [hit.content for hit in hits]))
        ordered = sorted(enumerate(scores), key=lambda pair: float(pair[1]), reverse=True)
        return [replace(hits[index], score=float(score), rerank_score=float(score))
                for index, score in ordered[:top_k]]
