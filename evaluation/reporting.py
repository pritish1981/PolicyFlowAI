"""Sanitized deterministic JSON and Markdown report helpers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def dataset_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_report(*, kind: str, dataset: str | Path, configuration: dict[str, Any],
                 aggregates: dict[str, Any], cases: list[dict[str, Any]],
                 thresholds: dict[str, float] | None = None, status: str,
                 errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "kind": kind,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {"path": str(dataset).replace("\\", "/"), "sha256": dataset_hash(dataset)},
        "configuration": configuration, "metric_version": "1.0",
        "aggregates": aggregates, "thresholds": thresholds or {}, "status": status,
        "case_results": cases, "errors": errors or [],
    }


def write_report(report: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
                      encoding="utf-8")
    return output


def write_summary(reports: list[tuple[str, Path, str]], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Phase 007 Evaluation Summary", "",
             "| Evaluation | Status | Report |", "|---|---|---|"]
    for label, report_path, status in reports:
        lines.append(f"| {label} | {status.upper()} | [{report_path.name}]({report_path.name}) |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output
