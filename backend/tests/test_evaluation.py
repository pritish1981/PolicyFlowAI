"""Phase 007 deterministic evaluation tests."""
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from evaluation.benchmark import benchmark
from evaluation.metrics import (
    CitationJudgment, citation_scores, evaluate_thresholds, precision_at_k,
    recall_at_k, reciprocal_rank, retrieval_metrics,
)
from evaluation.models import load_expense_cases, load_policy_cases
from evaluation.reporting import build_report, write_report, write_summary
from evaluation.run_decisions import evaluate as evaluate_decisions

ROOT = Path(__file__).resolve().parents[2]
POLICY_DATA = ROOT / "evaluation/datasets/policy_qa_golden.json"
EXPENSE_DATA = ROOT / "evaluation/datasets/expense_cases.json"


def test_versioned_datasets_are_valid_unique_and_complete():
    policies = load_policy_cases(POLICY_DATA)
    expenses = load_expense_cases(EXPENSE_DATA)
    assert len({case.id for case in policies}) == len(policies)
    assert {f"POL-00{number}" for number in range(1, 7)} <= {
        case.expected_policy_code for case in policies}
    assert any(case.expected_evidence_status == "INSUFFICIENT_INFORMATION"
               for case in policies)
    assert {case.expected_decision for case in expenses} == {
        "COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"}


def test_dataset_loader_identifies_duplicate_and_bad_cases(tmp_path):
    duplicate = [{"id": "same", "question": "valid?", "expected_policy_code": "POL-001",
                  "expected_relevant_ids": ["POL-001"], "required_fact": "x"}] * 2
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case IDs"):
        load_policy_cases(path)
    path.write_text(json.dumps([{"id": "bad", "question": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid case bad"):
        load_policy_cases(path)


def test_retrieval_metrics_exact_boundaries_and_empty_behavior():
    assert precision_at_k(["a", "x", "b", "y", "z"], {"a", "b"}, 5) == .4
    assert recall_at_k(["a", "x", "b"], {"a", "b"}, 10) == 1
    assert reciprocal_rank(["x", "b"], {"b"}) == .5
    assert recall_at_k([], set(), 10) == 1
    assert reciprocal_rank([], set()) == 1
    totals = retrieval_metrics([(["a"], {"a"}), ([], set())])
    assert totals["recall_at_10"] == 1


def test_citation_metrics_and_thresholds():
    valid = CitationJudgment("chunk", "POL-002", "domestic", True)
    assert citation_scores([valid], {"chunk"}, "POL-002", "domestic") == {
        "citation_correctness": 1.0, "valid_citation_coverage": 1.0, "failures": []}
    mismatch = citation_scores([valid], {"chunk"}, "POL-999")
    assert mismatch["citation_correctness"] == 0 and "policy_mismatch" in mismatch["failures"][0]
    assert evaluate_thresholds({"precision_at_5": .8}, {"precision_at_5": .8})["status"] == "pass"
    assert evaluate_thresholds({"precision_at_5": .79}, {"precision_at_5": .8})["status"] == "fail"


def test_decision_runner_is_exact_and_credential_free(tmp_path):
    report, code = evaluate_decisions(EXPENSE_DATA, tmp_path / "decisions.json")
    assert code == 0
    assert report["aggregates"]["decision_accuracy"] == 1.0
    assert report["status"] == "pass"


def test_reports_are_versioned_and_summary_links(tmp_path):
    report = build_report(kind="test", dataset=POLICY_DATA, configuration={},
                          aggregates={"score": 1}, cases=[], status="pass")
    output = write_report(report, tmp_path / "result.json")
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "1.0"
    assert len(loaded["dataset"]["sha256"]) == 64
    summary = write_summary([("Retrieval", output, "pass")], tmp_path / "SUMMARY.md")
    assert "[result.json](result.json)" in summary.read_text(encoding="utf-8")


def test_benchmark_uses_identical_cases_and_reports_fallback(tmp_path):
    cases = load_policy_cases(POLICY_DATA)
    relevant = {case.id: case.expected_policy_code for case in cases}
    calls = []

    def executor(strategy, query, _factory, **_kwargs):
        case = next(case for case in cases if case.question == query)
        calls.append((strategy, case.id))
        hits = [] if relevant[case.id] is None else [
            SimpleNamespace(policy_code=relevant[case.id], chunk_id=uuid4())]
        return SimpleNamespace(strategy=strategy, hits=hits, latency_ms=1.0,
                               fallback=strategy == "hybrid_rerank", available=True)

    report = benchmark(POLICY_DATA, tmp_path / "retrieval_benchmark.json",
                       session_factory=object(), executor=executor)
    expected_ids = [case.id for case in cases]
    assert all(value["case_ids"] == expected_ids for value in report["aggregates"].values())
    assert report["aggregates"]["hybrid_rerank"]["quality_label"] == "fallback"
    assert len(calls) == len(cases) * 3


def test_optional_evaluator_conversion_and_skip(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ENABLE_AI_EVALUATION", raising=False)
    from evaluation.ragas.evaluate_rag import build_ragas_rows, run as run_ragas
    from evaluation.deepeval.evaluate_agent import build_deepeval_rows, run as run_deepeval
    cases = load_policy_cases(POLICY_DATA)
    assert build_ragas_rows(cases)[0]["user_input"] == cases[0].question
    assert build_deepeval_rows(cases)[0]["input"] == cases[0].question
    assert run_ragas(POLICY_DATA, tmp_path / "ragas.json")[0]["status"] == "skip"
    assert run_deepeval(POLICY_DATA, tmp_path / "deepeval.json")[0]["status"] == "skip"


def test_runtime_has_no_evaluator_imports():
    for path in (ROOT / "backend/app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import ragas" not in text
        assert "import deepeval" not in text
