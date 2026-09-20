"""Optional offline DeepEval runner; never imported by application runtime."""
import argparse
import json
import os
from pathlib import Path

from evaluation.models import PolicyGoldenCase, load_policy_cases
from evaluation.reporting import build_report, write_report


def build_deepeval_rows(cases: list[PolicyGoldenCase],
                        generated: dict[str, dict] | None = None) -> list[dict]:
    generated = generated or {}
    return [{"input": case.question,
             "actual_output": generated.get(case.id, {}).get("answer", ""),
             "retrieval_context": generated.get(case.id, {}).get("contexts", []),
             "expected_output": case.required_fact or ""}
            for case in cases]


def run(dataset: Path, output: Path, results_path: Path | None = None) -> tuple[dict, int]:
    cases = load_policy_cases(dataset)
    if os.getenv("ENABLE_AI_EVALUATION", "").lower() not in {"1", "true", "yes"} or not os.getenv("OPENAI_API_KEY"):
        report = build_report(kind="deepeval", dataset=dataset,
                              configuration={"metrics": [
                                  "faithfulness", "answer_relevancy",
                                  "contextual_precision", "contextual_recall"]},
                              aggregates={}, cases=[], status="skip",
                              errors=["optional evaluator credentials are unavailable"])
        write_report(report, output)
        return report, 0
    if results_path is None or not results_path.exists():
        report = build_report(kind="deepeval", dataset=dataset,
                              configuration={"mode": "live", "metrics": [
                                  "faithfulness", "answer_relevancy",
                                  "contextual_precision", "contextual_recall"]},
                              aggregates={}, cases=[], status="skip",
                              errors=["a generated answer/context result bundle is required"])
        write_report(report, output)
        return report, 0
    generated = json.loads(results_path.read_text(encoding="utf-8"))
    from deepeval import evaluate
    from deepeval.metrics import (
        AnswerRelevancyMetric, ContextualPrecisionMetric, ContextualRecallMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase
    test_cases = [LLMTestCase(**row) for row in build_deepeval_rows(cases, generated)]
    result = evaluate(test_cases, metrics=[
        FaithfulnessMetric(), AnswerRelevancyMetric(),
        ContextualPrecisionMetric(), ContextualRecallMetric()])
    case_rows, scores = [], {}
    for case, test_result in zip(cases, result.test_results):
        row = {"case_id": case.id}
        for metric in test_result.metrics_data:
            name = metric.name.lower().replace(" ", "_")
            row[name] = metric.score
            if metric.score is not None:
                scores.setdefault(name, []).append(metric.score)
        case_rows.append(row)
    aggregates = {name: sum(values) / len(values) for name, values in scores.items()}
    report = build_report(kind="deepeval", dataset=dataset,
                          configuration={"mode": "live_baseline"},
                          aggregates=aggregates, cases=case_rows, status="baseline")
    write_report(report, output)
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path,
                        default=Path("evaluation/datasets/policy_qa_golden.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("evaluation/reports/deepeval.json"))
    parser.add_argument("--results", type=Path)
    args = parser.parse_args()
    return run(args.dataset, args.output, args.results)[1]


if __name__ == "__main__":
    raise SystemExit(main())
