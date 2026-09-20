"""Compare retrieval strategies over identical golden cases."""
import argparse
from pathlib import Path
from statistics import mean

from app.core.config import settings
from app.db.session import SessionLocal
from evaluation.metrics import retrieval_metrics
from evaluation.models import load_policy_cases
from evaluation.reporting import build_report, write_report
from evaluation.retrieval import ranked_policy_ids, run_strategy


class _UnavailableReranker:
    def rerank(self, *_args, **_kwargs):
        raise RuntimeError("benchmark reranker not explicitly configured")


def benchmark(dataset: Path, output: Path, session_factory=SessionLocal,
              reranker=None, executor=run_strategy) -> dict:
    cases = load_policy_cases(dataset)
    case_ids = [case.id for case in cases]
    strategy_reports = {}
    all_rows = []
    for strategy in ("vector", "hybrid", "hybrid_rerank"):
        inputs, latencies, rows = [], [], []
        for case in cases:
            result = executor(strategy, case.question, session_factory,
                              category=case.category, region=case.region,
                              travel_type=case.travel_type, reranker=reranker)
            ranked = ranked_policy_ids(result.hits)
            inputs.append((ranked, set(case.expected_relevant_ids)))
            latencies.append(result.latency_ms)
            row = {"case_id": case.id, "strategy": strategy,
                   "ranked_policy_ids": ranked, "latency_ms": result.latency_ms,
                   "fallback": result.fallback, "available": result.available}
            rows.append(row)
            all_rows.append(row)
        strategy_reports[strategy] = {
            **retrieval_metrics(inputs), "average_latency_ms": mean(latencies),
            "case_ids": case_ids,
            "quality_label": "fallback" if any(item["fallback"] for item in rows)
                             else "measured",
        }
    report = build_report(kind="retrieval_benchmark", dataset=dataset,
                          configuration={"strategies": list(strategy_reports)},
                          aggregates=strategy_reports, cases=all_rows, status="pass")
    write_report(report, output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path,
                        default=Path(settings.evaluation_dataset_path) / "policy_qa_golden.json")
    parser.add_argument("--output", type=Path,
                        default=Path(settings.evaluation_report_path) / "retrieval_benchmark.json")
    args = parser.parse_args()
    # The default benchmark is credential-free and labels the reranked arm as a
    # fallback. Operators may inject an explicit reranker from a controlled script.
    benchmark(args.dataset, args.output, reranker=_UnavailableReranker())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
