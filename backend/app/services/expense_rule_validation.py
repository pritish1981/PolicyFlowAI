"""Reject model rule facts that cannot be verified against selected stored evidence."""
import re
from datetime import date
from decimal import Decimal
from sqlalchemy import select

from app.models.policy_chunk import PolicyChunk
from app.models.policy_document import PolicyDocument
from app.rag.citations.validator import Citation, validate_citations
from app.rag.retrieval.rrf import SearchHit
from app.schemas.expense import PolicyRuleSet, RuleType
from app.services.expense_evidence import CATEGORY
from app.schemas.expense import ExpenseType


def validated_rules(ruleset: PolicyRuleSet, hits: list[SearchHit], session_factory,
                    as_of: date, expense_type: ExpenseType | None = None,
                    travel_type: str | None = None) -> tuple[PolicyRuleSet | None, list[Citation]]:
    if ruleset.insufficient_information or not ruleset.rules or not hits:
        return None, []
    by_id = {hit.chunk_id: hit for hit in hits}
    ids = {source for rule in ruleset.rules for source in rule.source_chunk_ids}
    if not ids or not ids <= by_id.keys():
        return None, []
    for rule in ruleset.rules:
        sources = [by_id[source] for source in rule.source_chunk_ids]
        if expense_type is not None:
            expected = CATEGORY[expense_type]
            if rule.rule_type == RuleType.AMOUNT_LIMIT and rule.category != expected:
                return None, []
            if rule.rule_type == RuleType.REVIEW_REQUIRED and rule.category not in (expected, "EXPENSE_EXCEPTION"):
                return None, []
            if rule.rule_type == RuleType.RECEIPT_REQUIRED and rule.category not in (expected, "DOCUMENTATION"):
                return None, []
        if travel_type and rule.travel_type and rule.travel_type.value != travel_type:
            # A rule for another travel type may be present in evidence, but
            # it cannot be used as an applicable threshold for this expense.
            continue
        if rule.rule_type in (RuleType.AMOUNT_LIMIT, RuleType.RECEIPT_REQUIRED):
            assert rule.amount_limit is not None
            amounts = [Decimal(value.replace(",", "")) for hit in sources
                       for value in re.findall(r"\bINR\s*([\d,]+(?:\.\d{1,2})?)\b", hit.content, re.I)]
            if rule.amount_limit not in amounts:
                return None, []
        if rule.rule_type == RuleType.AMOUNT_LIMIT and rule.unit:
            phrase = {"PER_NIGHT": "per night", "PER_DAY": "per day",
                      "PER_TRIP": "per trip", "PER_TRANSACTION": "per transaction"}[rule.unit]
            if not any(phrase in hit.content.lower() or
                       (phrase == "per trip" and "one-way trip" in hit.content.lower())
                       for hit in sources):
                return None, []
        if rule.rule_type == RuleType.RECEIPT_REQUIRED and not any(
            "receipt" in hit.content.lower() for hit in sources
        ):
            return None, []
        if rule.rule_type == RuleType.REVIEW_REQUIRED and not any(
            "review" in (hit.content + " " + hit.section_title).lower()
            and ("exception" in hit.content.lower() or "above" in hit.content.lower())
            for hit in sources
        ):
            return None, []
        if rule.rule_type == RuleType.PROHIBITION and (
            not rule.condition or not any(rule.condition.casefold() in hit.content.casefold()
                                          for hit in sources)
        ):
            return None, []
    with session_factory() as session:
        if expense_type is not None:
            domains = dict(session.execute(
                select(PolicyChunk.id, PolicyDocument.domain)
                .join(PolicyDocument).where(PolicyChunk.id.in_(ids))
            ).all())
            for rule in ruleset.rules:
                allowed = ({CATEGORY[expense_type]} if rule.rule_type == RuleType.AMOUNT_LIMIT
                           else {"DOCUMENTATION", CATEGORY[expense_type]}
                           if rule.rule_type == RuleType.RECEIPT_REQUIRED
                           else {"EXPENSE_EXCEPTION", CATEGORY[expense_type]})
                if any(domains.get(source) not in allowed for source in rule.source_chunk_ids):
                    return None, []
        citations = validate_citations(hits, session, as_of,
                                       retrieved_ids=set(by_id), cited_ids=ids)
    if {citation.chunk_id for citation in citations} != ids:
        return None, []
    return ruleset, citations
