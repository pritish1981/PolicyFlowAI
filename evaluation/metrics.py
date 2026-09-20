"""Credential-free deterministic retrieval, citation, and decision metrics."""
from dataclasses import dataclass
from statistics import mean

from evaluation.models import ExpenseGoldenCase


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if not ranked:
        return 0.0
    window = ranked[:k]
    return sum(item in relevant for item in window) / k


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    if not relevant:
        return 1.0 if not ranked else 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for rank, item in enumerate(ranked, start=1):
        if item in relevant:
            return 1.0 / rank
    return 1.0 if not relevant and not ranked else 0.0


def retrieval_metrics(results: list[tuple[list[str], set[str]]]) -> dict[str, float]:
    if not results:
        return {"precision_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0}
    return {
        "precision_at_5": mean(precision_at_k(ranked, relevant, 5)
                               for ranked, relevant in results),
        "recall_at_10": mean(recall_at_k(ranked, relevant, 10)
                             for ranked, relevant in results),
        "mrr": mean(reciprocal_rank(ranked, relevant) for ranked, relevant in results),
    }


@dataclass(frozen=True)
class CitationJudgment:
    chunk_id: str
    policy_code: str
    section_id: str
    eligible: bool = True


def citation_scores(citations: list[CitationJudgment], retrieved_ids: set[str],
                    expected_policy: str | None, expected_section: str | None = None
                    ) -> dict[str, object]:
    failures: list[str] = []
    valid = 0
    for citation in citations:
        if citation.chunk_id not in retrieved_ids:
            failures.append(f"{citation.chunk_id}:not_retrieved")
        elif not citation.eligible:
            failures.append(f"{citation.chunk_id}:ineligible")
        elif expected_policy and citation.policy_code != expected_policy:
            failures.append(f"{citation.chunk_id}:policy_mismatch")
        elif expected_section and citation.section_id != expected_section:
            failures.append(f"{citation.chunk_id}:section_mismatch")
        else:
            valid += 1
    correctness = valid / len(citations) if citations else (1.0 if expected_policy is None else 0.0)
    coverage = 1.0 if expected_policy is None or valid else 0.0
    return {"citation_correctness": correctness, "valid_citation_coverage": coverage,
            "failures": failures}


def decision_accuracy(expected: list[ExpenseGoldenCase], actual: dict[str, dict]) -> dict[str, object]:
    failures: list[str] = []
    for case in expected:
        result = actual.get(case.id)
        if result is None:
            failures.append(f"{case.id}:missing")
            continue
        actual_limit = None if result.get("policy_limit") is None else str(result["policy_limit"])
        expected_limit = None if case.expected_limit is None else str(case.expected_limit)
        if result.get("decision") != case.expected_decision or actual_limit != expected_limit:
            failures.append(case.id)
        if sorted(result.get("sources", [])) != sorted(case.expected_sources):
            failures.append(f"{case.id}:source_mismatch")
    passed = len(expected) - len({item.split(":")[0] for item in failures})
    return {"decision_accuracy": passed / len(expected) if expected else 0.0,
            "failures": failures}


def evaluate_thresholds(metrics: dict[str, float], thresholds: dict[str, float]) -> dict[str, object]:
    failures = {name: {"actual": metrics.get(name), "required": minimum}
                for name, minimum in thresholds.items()
                if metrics.get(name, float("-inf")) < minimum}
    return {"status": "pass" if not failures else "fail", "failures": failures}
