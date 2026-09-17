"""Cohere Rerank adapter."""
from dataclasses import replace
from app.rag.retrieval.rrf import SearchHit


class CohereReranker:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("COHERE_API_KEY is required")
        self.api_key = api_key
        self.model = model

    def rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        if not hits:
            return []
        import cohere
        response = cohere.ClientV2(api_key=self.api_key).rerank(
            model=self.model, query=query, documents=[hit.content for hit in hits],
            top_n=min(top_k, len(hits)),
        )
        return [replace(hits[item.index], score=float(item.relevance_score),
                        rerank_score=float(item.relevance_score)) for item in response.results]
