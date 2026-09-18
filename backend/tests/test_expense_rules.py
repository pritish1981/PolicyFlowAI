"""Pure deterministic expense decisions from verified policy facts."""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.rules.expense_rules import evaluate_expense_rules
from app.schemas.expense import Decision, ExpenseCreate, PolicyRuleSet


def inputs(kind="HOTEL", amount="6500", receipt=True, purpose="Client meeting",
           travel="DOMESTIC"):
    return ExpenseCreate(expense_type=kind, amount=amount, currency="INR",
                         location="Bengaluru", travel_type=travel,
                         purpose=purpose, receipt_available=receipt)


def verified_rules(kind="HOTEL", limit="7000", travel="DOMESTIC", receipt="500",
                   review=True, prohibited=None):
    category = {"HOTEL": "HOTEL", "MEAL": "MEAL", "TAXI": "GROUND_TRANSPORTATION"}[kind]
    unit = {"HOTEL": "PER_NIGHT", "MEAL": "PER_DAY", "TAXI": "PER_TRIP"}[kind]
    rules = [
        {"rule_type": "AMOUNT_LIMIT", "category": category, "amount_limit": limit,
         "currency": "INR", "unit": unit, "travel_type": travel,
         "source_chunk_ids": [uuid4()]},
        {"rule_type": "RECEIPT_REQUIRED", "category": "DOCUMENTATION",
         "amount_limit": receipt, "currency": "INR", "unit": "PER_TRANSACTION",
         "source_chunk_ids": [uuid4()]},
    ]
    if review:
        rules.append({"rule_type": "REVIEW_REQUIRED", "category": "EXPENSE_EXCEPTION",
                      "source_chunk_ids": [uuid4()]})
    if prohibited:
        rules.append({"rule_type": "PROHIBITION", "category": category,
                      "condition": prohibited, "source_chunk_ids": [uuid4()]})
    typed = PolicyRuleSet.model_validate({"rules": rules})
    return typed, {identifier for rule in typed.rules for identifier in rule.source_chunk_ids}


@pytest.mark.parametrize("kind,amount,limit,travel,expected", [
    ("HOTEL", "6500", "7000", "DOMESTIC", Decision.COMPLIANT),
    ("HOTEL", "9500", "7000", "DOMESTIC", Decision.NEEDS_REVIEW),
    ("HOTEL", "14000", "15000", "INTERNATIONAL", Decision.COMPLIANT),
    ("HOTEL", "17000", "15000", "INTERNATIONAL", Decision.NEEDS_REVIEW),
    ("MEAL", "1200", "1500", "DOMESTIC", Decision.COMPLIANT),
    ("MEAL", "1800", "1500", "DOMESTIC", Decision.NEEDS_REVIEW),
    ("TAXI", "1500", "2000", "DOMESTIC", Decision.COMPLIANT),
    ("TAXI", "2500", "2000", "DOMESTIC", Decision.NEEDS_REVIEW),
])
def test_thresholds_are_data_not_engine_constants(kind, amount, limit, travel, expected):
    rules, ids = verified_rules(kind, limit, travel)
    result = evaluate_expense_rules(inputs(kind, amount, travel=travel), rules, ids)
    assert result.decision == expected
    assert result.policy_limit == Decimal(limit)
    assert result.confidence == Decimal("1")
    if expected == Decision.NEEDS_REVIEW:
        assert result.next_action == "SUBMIT_EXCEPTION_JUSTIFICATION"


def test_receipt_boundary_and_prohibition():
    rules, ids = verified_rules()
    assert evaluate_expense_rules(inputs(amount="500", receipt=False), rules, ids).decision == Decision.COMPLIANT
    assert evaluate_expense_rules(inputs(amount="501", receipt=False), rules, ids).decision == Decision.NON_COMPLIANT
    rules, ids = verified_rules(prohibited="personal upgrade")
    assert evaluate_expense_rules(inputs(purpose="personal upgrade"), rules, ids).decision == Decision.NON_COMPLIANT


def test_incomplete_conflicting_or_unverified_evidence_abstains():
    rules, ids = verified_rules()
    assert evaluate_expense_rules(inputs(), None, ids).decision == Decision.INSUFFICIENT_INFORMATION
    assert evaluate_expense_rules(inputs(), rules, set()).decision == Decision.INSUFFICIENT_INFORMATION
    rules.rules.append(rules.rules[0].model_copy(update={"amount_limit": Decimal("9000")}))
    assert evaluate_expense_rules(inputs(), rules, ids).decision == Decision.INSUFFICIENT_INFORMATION
    rules, ids = verified_rules(review=False)
    assert evaluate_expense_rules(inputs(amount="9500"), rules, ids).decision == Decision.INSUFFICIENT_INFORMATION
