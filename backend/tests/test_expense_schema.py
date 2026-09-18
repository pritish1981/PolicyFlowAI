"""Expense intake and model-rule boundary tests."""
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseClarification, ExpenseCreate, PolicyRule, RuleType


@pytest.mark.parametrize("kind", ["HOTEL", "MEAL", "TAXI"])
def test_expense_intake_preserves_decimal(kind):
    item = ExpenseCreate(expense_type=kind, amount="9500.00", currency="INR",
                         location=" Bengaluru ", travel_type="DOMESTIC",
                         purpose="Client meeting", receipt_available=True)
    assert item.amount == Decimal("9500.00")
    assert item.location == "Bengaluru"
    assert item.missing_fields() == []


@pytest.mark.parametrize("field,value", [
    ("expense_type", "FLIGHT"), ("travel_type", "SPACE"),
    ("amount", "0"), ("amount", "-1"), ("amount", "1.234"),
    ("currency", "USD"), ("purpose", "   "),
])
def test_invalid_supplied_value_rejected(field, value):
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate({field: value})


def test_missing_fields_and_unknown_fields():
    assert ExpenseCreate(expense_type="HOTEL").missing_fields() == [
        "amount", "currency", "location", "travel_type", "purpose", "receipt_available"]
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate({"unsupported": True})
    with pytest.raises(ValidationError):
        ExpenseClarification.model_validate({})


def test_policy_rule_requires_typed_money_and_source():
    rule = PolicyRule(rule_type=RuleType.AMOUNT_LIMIT, category="HOTEL",
                      amount_limit="7000.00", currency="INR", unit="PER_NIGHT",
                      source_chunk_ids=[uuid4()])
    assert rule.amount_limit == Decimal("7000.00")
    with pytest.raises(ValidationError):
        PolicyRule(rule_type="APPROVE", category="HOTEL", source_chunk_ids=[])
