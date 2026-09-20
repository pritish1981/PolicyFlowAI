"""Credential-free exact expense-decision evaluation."""
import argparse
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.core.config import settings
from app.rules.expense_rules import evaluate_expense_rules
from app.schemas.expense import ExpenseCreate, PolicyRuleSet
from evaluation.metrics import decision_accuracy, evaluate_thresholds
from evaluation.models import ExpenseGoldenCase, load_expense_cases
from evaluation.reporting import build_report, write_report


def _rule_id(case_id: str, name: str):
    return uuid5(NAMESPACE_URL, f"policyflow:{case_id}:{name}")


def evaluate_case(case: ExpenseGoldenCase) -> dict:
    expense = ExpenseCreate(expense_type=case.expense_type, amount=case.amount, currency="INR",
                            location="Golden fixture", travel_type=case.travel_type,
                            purpose="Controlled business travel",
                            receipt_available=case.receipt_available)
    if case.expected_decision == "INSUFFICIENT_INFORMATION":
        assessment = evaluate_expense_rules(expense, None, set())
        return {"decision": assessment.decision.value, "policy_limit": None,
                "sources": case.expected_sources}
    category = {"HOTEL": "HOTEL", "MEAL": "MEAL",
                "TAXI": "GROUND_TRANSPORTATION"}[case.expense_type]
    unit = {"HOTEL": "PER_NIGHT", "MEAL": "PER_DAY", "TAXI": "PER_TRIP"}[case.expense_type]
    ids = {name: _rule_id(case.id, name) for name in ("limit", "receipt", "review")}
    ruleset = PolicyRuleSet.model_validate({"rules": [
        {"rule_type": "AMOUNT_LIMIT", "category": category,
         "amount_limit": case.expected_limit, "currency": "INR", "unit": unit,
         "travel_type": case.travel_type, "source_chunk_ids": [ids["limit"]]},
        {"rule_type": "RECEIPT_REQUIRED", "category": "DOCUMENTATION",
         "amount_limit": Decimal("500"), "currency": "INR", "unit": "PER_TRANSACTION",
         "source_chunk_ids": [ids["receipt"]]},
        {"rule_type": "REVIEW_REQUIRED", "category": "EXPENSE_EXCEPTION",
         "source_chunk_ids": [ids["review"]]},
    ]})
    assessment = evaluate_expense_rules(expense, ruleset, set(ids.values()))
    return {"decision": assessment.decision.value,
            "policy_limit": assessment.policy_limit, "sources": case.expected_sources}


def evaluate(dataset: Path, output: Path) -> tuple[dict, int]:
    cases = load_expense_cases(dataset)
    actual = {case.id: evaluate_case(case) for case in cases}
    aggregates = decision_accuracy(cases, actual)
    thresholds = {"decision_accuracy": settings.evaluation_decision_accuracy_threshold}
    gate = evaluate_thresholds({"decision_accuracy": aggregates["decision_accuracy"]}, thresholds)
    rows = [{"case_id": case.id, "expected_decision": case.expected_decision,
             **actual[case.id]} for case in cases]
    report = build_report(kind="expense_decisions", dataset=dataset,
                          configuration={"judge": "deterministic_rules"},
                          aggregates=aggregates, cases=rows, thresholds=thresholds,
                          status=gate["status"], errors=aggregates["failures"])
    write_report(report, output)
    return report, 0 if gate["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path,
                        default=Path(settings.evaluation_dataset_path) / "expense_cases.json")
    parser.add_argument("--output", type=Path,
                        default=Path(settings.evaluation_report_path) / "expense_decisions.json")
    args = parser.parse_args()
    return evaluate(args.dataset, args.output)[1]


if __name__ == "__main__":
    raise SystemExit(main())
