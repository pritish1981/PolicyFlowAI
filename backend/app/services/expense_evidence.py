"""Reuse eligible hybrid policy evidence for an expense assessment."""
from dataclasses import dataclass
from datetime import date
from typing import Callable
import re

from app.core.config import settings
from app.rag.reranking import rerank
from app.rag.retrieval.hybrid_retriever import HybridResults, policy_qa_filters, retrieve
from app.rag.retrieval.rrf import SearchHit, fuse
from app.schemas.expense import ExpenseCreate, ExpenseType


CATEGORY = {
    ExpenseType.HOTEL: "HOTEL",
    ExpenseType.MEAL: "MEAL",
    ExpenseType.TAXI: "GROUND_TRANSPORTATION",
}


@dataclass(frozen=True)
class ExpenseEvidence:
    lexical_hits: list[SearchHit]
    vector_hits: list[SearchHit]
    fused_hits: list[SearchHit]
    reranked_hits: list[SearchHit]
    category_counts: dict[str, int]


def gather_expense_evidence(
    expense: ExpenseCreate, session_factory, *, assessment_date: date,
    retriever: Callable = retrieve, reranker=None,
) -> ExpenseEvidence:
    if expense.expense_type is None or expense.travel_type is None:
        raise ValueError("complete expense required for retrieval")
    categories = [CATEGORY[expense.expense_type], "DOCUMENTATION", "EXPENSE_EXCEPTION"]
    lexical: list[SearchHit] = []
    vector: list[SearchHit] = []
    lexical_by: dict[str, list[SearchHit]] = {}
    vector_by: dict[str, list[SearchHit]] = {}
    by_category: dict[str, list[SearchHit]] = {}
    for category in categories:
        query = (f"{expense.travel_type.value} {expense.expense_type.value} "
                 f"{category} standard limit receipt mandatory exception review")
        results: HybridResults = retriever(
            query, session_factory,
            filters=policy_qa_filters(category, "INDIA" if expense.travel_type.value == "DOMESTIC" else None,
                                      assessment_date),
            travel_type=expense.travel_type.value,
        )
        lexical.extend(results.lexical_hits)
        vector.extend(results.vector_hits)
        lexical_by[category] = results.lexical_hits
        vector_by[category] = results.vector_hits
        by_category[category] = fuse([results.lexical_hits, results.vector_hits],
                                     settings.rrf_k, settings.retrieval_top_n)

    # Interleave categories so one corpus cannot bury all other candidates.
    def interleave(groups: list[list[SearchHit]]) -> list[SearchHit]:
        ordered: list[SearchHit] = []
        seen = set()
        for index in range(max((len(group) for group in groups), default=0)):
            for group in groups:
                if index < len(group) and group[index].chunk_id not in seen:
                    ordered.append(group[index])
                    seen.add(group[index].chunk_id)
        return ordered

    category_hits = [by_category[category] for category in categories]
    fused = fuse([interleave([lexical_by[category] for category in categories]),
                  interleave([vector_by[category] for category in categories])],
                 settings.rrf_k, settings.retrieval_top_n)
    # Reserve relevant evidence from each category in the bounded final packet.
    ranked = rerank(" ".join(categories) + " " + expense.travel_type.value,
                    interleave(category_hits)[:settings.retrieval_top_n], reranker)
    selected: list[SearchHit] = []
    def coverage(hit: SearchHit, category: str) -> int:
        body = " ".join(hit.content.lower().split())
        if category == categories[0]:
            scope = (expense.travel_type.value.lower() in body or
                     (expense.travel_type.value == "DOMESTIC" and "within india" in body))
            return int(bool(re.search(r"(?:standard.{0,90}|reimbursable )limit is.{0,30}inr|standard reimbursable.{0,90}inr", body))
                       and scope)
        if category == "DOCUMENTATION":
            return int("receipt" in body and "mandatory" in body and "greater than inr" in body)
        return int("review" in body and "above" in body and "inr" in body)

    for category in categories:
        category_ranked = rerank(category, by_category[category], reranker)
        category_ranked = sorted(category_ranked,
                                 key=lambda hit: -coverage(hit, category))
        if category_ranked and category_ranked[0].chunk_id not in {item.chunk_id for item in selected}:
            selected.append(category_ranked[0])
    for hit in ranked:
        if hit.chunk_id not in {item.chunk_id for item in selected}:
            selected.append(hit)
        if len(selected) >= settings.rerank_top_k:
            break
    return ExpenseEvidence(lexical, vector, fused, selected[:settings.rerank_top_k],
                           {category: len(by_category[category]) for category in categories})
