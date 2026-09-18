"""Make financial policy decisions from verified rules, never model conclusions."""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.schemas.expense import (
    Decision, ExpenseCreate, PolicyRule, PolicyRuleSet, RuleType,
)
from app.services.expense_evidence import CATEGORY


@dataclass(frozen=True)
class RuleEvaluation:
    decision: Decision
    policy_limit: Decimal | None
    confidence: Decimal
    explanation: str
    next_action: str


def _insufficient(reason: str) -> RuleEvaluation:
    return RuleEvaluation(Decision.INSUFFICIENT_INFORMATION, None, Decimal("0"),
                          reason, "PROVIDE_CLARIFICATION")


def evaluate_expense_rules(expense: ExpenseCreate, ruleset: PolicyRuleSet | None,
                           valid_citation_ids: set[UUID]) -> RuleEvaluation:
    if expense.missing_fields() or not ruleset or ruleset.insufficient_information:
        return _insufficient("Required expense or policy information is missing.")
    if not valid_citation_ids or any(
        not set(rule.source_chunk_ids) <= valid_citation_ids for rule in ruleset.rules
    ):
        return _insufficient("Policy sources could not be verified.")
    assert expense.expense_type is not None
    assert expense.amount is not None
    assert expense.travel_type is not None
    assert expense.currency is not None
    expected_category = CATEGORY[expense.expense_type]
    applicable = [rule for rule in ruleset.rules if
                  rule.travel_type is None or rule.travel_type == expense.travel_type]
    amount_rules = [rule for rule in applicable if rule.rule_type == RuleType.AMOUNT_LIMIT
                    and rule.category == expected_category and rule.currency == expense.currency]
    receipt_rules = [rule for rule in applicable if rule.rule_type == RuleType.RECEIPT_REQUIRED
                     and rule.currency == expense.currency]
    review_rules = [rule for rule in applicable if rule.rule_type == RuleType.REVIEW_REQUIRED]
    if len({(rule.amount_limit, rule.unit) for rule in amount_rules}) != 1:
        return _insufficient("The applicable amount limit is missing or conflicting.")
    if len({rule.amount_limit for rule in receipt_rules}) != 1:
        return _insufficient("The receipt requirement is missing or conflicting.")
    amount_rule = amount_rules[0]
    receipt_rule = receipt_rules[0]
    expected_unit = {"HOTEL": "PER_NIGHT", "MEAL": "PER_DAY", "TAXI": "PER_TRIP"}[
        expense.expense_type.value]
    if amount_rule.unit != expected_unit:
        return _insufficient("The policy amount unit does not match the expense.")
    assert amount_rule.amount_limit is not None
    assert receipt_rule.amount_limit is not None
    for rule in applicable:
        if (rule.rule_type == RuleType.PROHIBITION and rule.condition
                and rule.condition.casefold() in (expense.purpose or "").casefold()):
            return RuleEvaluation(Decision.NON_COMPLIANT, amount_rule.amount_limit,
                                  Decimal("1"), "The cited policy prohibits this purpose.", "NONE")
    if expense.amount > receipt_rule.amount_limit and not expense.receipt_available:
        return RuleEvaluation(Decision.NON_COMPLIANT, amount_rule.amount_limit,
                              Decimal("1"), "A mandatory receipt is missing.", "NONE")
    if expense.amount > amount_rule.amount_limit:
        if not review_rules:
            return _insufficient("Exception handling is not supported by verified evidence.")
        return RuleEvaluation(Decision.NEEDS_REVIEW, amount_rule.amount_limit,
                              Decimal("1"), "The amount exceeds the standard policy limit; human exception review is required.",
                              "SUBMIT_EXCEPTION_JUSTIFICATION")
    return RuleEvaluation(Decision.COMPLIANT, amount_rule.amount_limit, Decimal("1"),
                          "The amount is within the cited standard limit and required documentation is present.",
                          "NONE")
