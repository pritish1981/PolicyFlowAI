"""Run deterministic retrieval evaluation against configured PostgreSQL."""
import argparse
from datetime import date
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal
from evaluation.metrics import (
    CitationJudgment, citation_scores, evaluate_thresholds, retrieval_metrics,
)
from evaluation.models import load_policy_cases
from evaluation.reporting import build_report, write_report
from evaluation.retrieval import ranked_policy_ids, run_strategy


def evaluate(strategy: str, dataset: Path, output: Path,
             session_factory=SessionLocal, reranker=None) -> tuple[dict, int]:
    cases = load_policy_cases(dataset)
    rows, metric_input, citation_rows = [], [], []
    for case in cases:
        result = run_strategy(strategy, case.question, session_factory,
                              category=case.category, region=case.region,
                              travel_type=case.travel_type, as_of=date.today(),
                              reranker=reranker)
        ranked = ranked_policy_ids(result.hits)
        relevant = set(case.expected_relevant_ids)
        metric_input.append((ranked, relevant))
        rows.append({"case_id": case.id, "ranked_policy_ids": ranked,
                     "expected_relevant_ids": sorted(relevant),
                     "latency_ms": result.latency_ms, "fallback": result.fallback,
                     "available": result.available})
        candidate = next((hit for hit in result.hits
                          if hit.policy_code == case.expected_policy_code), None)
        judgments = ([] if candidate is None else [CitationJudgment(
            str(candidate.chunk_id), candidate.policy_code, candidate.section_id, True)])
        citation = citation_scores(
            judgments, {str(hit.chunk_id) for hit in result.hits},
            case.expected_policy_code, case.expected_section_id)
        citation_rows.append({
            "case_id": case.id, "expected_policy_code": case.expected_policy_code,
            "expected_section_id": case.expected_section_id,
            "actual_section_id": candidate.section_id if candidate else None,
            **citation,
        })
    aggregates = retrieval_metrics(metric_input)
    citation_aggregates = {
        "citation_correctness": sum(row["citation_correctness"] for row in citation_rows) / len(citation_rows),
        "valid_citation_coverage": sum(row["valid_citation_coverage"] for row in citation_rows) / len(citation_rows),
    }
    thresholds = {"precision_at_5": settings.evaluation_precision_at_5_threshold,
                  "recall_at_10": settings.evaluation_recall_at_10_threshold,
                  "citation_correctness": settings.evaluation_citation_correctness_threshold}
    gate = evaluate_thresholds({**aggregates, **citation_aggregates}, thresholds)
    report = build_report(kind="retrieval", dataset=dataset,
                          configuration={"strategy": strategy}, aggregates=aggregates,
                          cases=rows, thresholds=thresholds, status=gate["status"],
                          errors=list(gate["failures"]))
    write_report(report, output)
    citation_report = build_report(
        kind="citation", dataset=dataset, configuration={"strategy": strategy},
        aggregates=citation_aggregates, cases=citation_rows,
        thresholds={"citation_correctness": thresholds["citation_correctness"]},
        status=("pass" if citation_aggregates["citation_correctness"] >=
                thresholds["citation_correctness"] else "fail"),
        errors=[failure for row in citation_rows for failure in row["failures"]])
    write_report(citation_report, output.with_name("citation_evaluation.json"))
    return report, 0 if gate["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=["vector", "hybrid", "hybrid_rerank"],
                        default="hybrid")
    parser.add_argument("--dataset", type=Path,
                        default=Path(settings.evaluation_dataset_path) / "policy_qa_golden.json")
    parser.add_argument("--output", type=Path,
                        default=Path(settings.evaluation_report_path) / "retrieval_evaluation.json")
    args = parser.parse_args()
    return evaluate(args.strategy, args.dataset, args.output)[1]


if __name__ == "__main__":
    raise SystemExit(main())
