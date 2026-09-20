"""Optional offline Ragas runner; never imported by application runtime."""
import argparse
import json
import os
from pathlib import Path

from evaluation.models import PolicyGoldenCase, load_policy_cases
from evaluation.reporting import build_report, write_report


def build_ragas_rows(cases: list[PolicyGoldenCase],
                     generated: dict[str, dict] | None = None) -> list[dict]:
    generated = generated or {}
    return [{"user_input": case.question,
             "response": generated.get(case.id, {}).get("answer", ""),
             "retrieved_contexts": generated.get(case.id, {}).get("contexts", []),
             "reference": case.required_fact or ""}
            for case in cases]


def run(dataset: Path, output: Path, results_path: Path | None = None) -> tuple[dict, int]:
    cases = load_policy_cases(dataset)
    if os.getenv("ENABLE_AI_EVALUATION", "").lower() not in {"1", "true", "yes"} or not os.getenv("OPENAI_API_KEY"):
        report = build_report(kind="ragas", dataset=dataset,
                              configuration={"metrics": [
                                  "faithfulness", "answer_relevancy",
                                  "context_precision", "context_recall"]},
                              aggregates={}, cases=[], status="skip",
                              errors=["optional evaluator credentials are unavailable"])
        write_report(report, output)
        return report, 0
    if results_path is None or not results_path.exists():
        report = build_report(kind="ragas", dataset=dataset,
                              configuration={"mode": "live", "metrics": [
                                  "faithfulness", "answer_relevancy",
                                  "context_precision", "context_recall"]},
                              aggregates={}, cases=[], status="skip",
                              errors=["a generated answer/context result bundle is required"])
        write_report(report, output)
        return report, 0
    generated = json.loads(results_path.read_text(encoding="utf-8"))
    from ragas import EvaluationDataset, evaluate
    from ragas.metrics import (
        AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness,
    )
    result = evaluate(
        EvaluationDataset.from_list(build_ragas_rows(cases, generated)),
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
        raise_exceptions=False, show_progress=False,
    )
    frame = result.to_pandas()
    metric_names = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    case_rows = [{"case_id": case.id, **{
        name: (None if name not in frame or frame.iloc[index][name] != frame.iloc[index][name]
               else float(frame.iloc[index][name]))
        for name in metric_names}} for index, case in enumerate(cases)]
    aggregates = {name: float(frame[name].dropna().mean())
                  for name in metric_names if name in frame}
    report = build_report(kind="ragas", dataset=dataset,
                          configuration={"mode": "live_baseline", "metrics": metric_names},
                          aggregates=aggregates, cases=case_rows, status="baseline")
    write_report(report, output)
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path,
                        default=Path("evaluation/datasets/policy_qa_golden.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("evaluation/reports/ragas.json"))
    parser.add_argument("--results", type=Path)
    args = parser.parse_args()
    return run(args.dataset, args.output, args.results)[1]


if __name__ == "__main__":
    raise SystemExit(main())
