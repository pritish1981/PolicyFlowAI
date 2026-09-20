"""Build a concise index for generated Phase 007 reports."""
import json
from pathlib import Path

from evaluation.reporting import write_summary


def main() -> int:
    report_dir = Path("evaluation/reports")
    entries = []
    labels = {
        "expense_decisions.json": "Expense decisions",
        "retrieval_evaluation.json": "Retrieval",
        "retrieval_benchmark.json": "Retrieval benchmark",
        "citation_evaluation.json": "Citations",
        "ragas.json": "Ragas",
        "deepeval.json": "DeepEval",
    }
    for name, label in labels.items():
        path = report_dir / name
        if path.exists():
            status = json.loads(path.read_text(encoding="utf-8")).get("status", "unknown")
            entries.append((label, path, status))
    write_summary(entries, report_dir / "SUMMARY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
