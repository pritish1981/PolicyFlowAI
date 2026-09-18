"""Credential-free structured extraction and source validation."""
import asyncio
import pytest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.gateway.model_gateway import ModelContext, ModelGateway
from app.core.exceptions import ModelUnavailableError, StructuredOutputError
from app.gateway.prompts import EXPENSE_RULE_SYSTEM_PROMPT, build_expense_rule_messages
from app.gateway.providers.base import ProviderResult
from app.gateway.routing import ModelTask
from app.rag.retrieval.rrf import SearchHit
from app.schemas.expense import PolicyRuleSet
from app.services.expense_rule_validation import validated_rules


class FakeProvider:
    async def generate_structured(self, *, messages, output_schema, model, max_output_tokens):
        del messages, max_output_tokens
        return ProviderResult(output=output_schema.model_validate({
            "rules": [{"rule_type": "AMOUNT_LIMIT", "category": "HOTEL",
                       "amount_limit": "7000", "currency": "INR", "unit": "PER_NIGHT",
                       "source_chunk_ids": [str(self.hit.chunk_id)]}],
        }), provider="fake", model=model)


def test_gateway_extracts_rules_without_decision():
    hit = SearchHit(uuid4(), "POL-002", "1.0", "domestic", "Domestic Hotel Limit",
                    "Domestic hotel INR 7,000 per night")
    provider = FakeProvider()
    provider.hit = hit
    messages = build_expense_rule_messages({"expense_type": "HOTEL", "amount": "6500",
                                             "travel_type": "DOMESTIC"}, [hit])
    assert "Never output COMPLIANT" in EXPENSE_RULE_SYSTEM_PROMPT
    assert str(hit.chunk_id) in messages[1]["content"]
    result = asyncio.run(ModelGateway(provider).invoke_structured(
        task=ModelTask.EXPENSE_POLICY_RULE, messages=messages,
        output_schema=PolicyRuleSet, context=ModelContext(request_id="r")))
    assert result.output.rules[0].amount_limit == Decimal("7000")
    assert "decision" not in type(result.output).model_fields


def test_rule_source_must_be_selected_and_numeric_supported(monkeypatch):
    hit = SearchHit(uuid4(), "POL-002", "1.0", "domestic", "Domestic Hotel Limit",
                    "Domestic hotel INR 7,000 per night")
    accepted = SimpleNamespace(chunk_id=hit.chunk_id)
    monkeypatch.setattr("app.services.expense_rule_validation.validate_citations",
                        lambda *_args, **_kwargs: [accepted])
    class FakeSession:
        def __enter__(self): return self
        def __exit__(self, *_args): return None

    def rules(amount, source):
        return PolicyRuleSet.model_validate({"rules": [{
            "rule_type": "AMOUNT_LIMIT", "category": "HOTEL", "amount_limit": amount,
            "currency": "INR", "source_chunk_ids": [str(source)]}]})

    assert validated_rules(rules("7000", hit.chunk_id), [hit], FakeSession,
                           date(2026, 9, 17))[0] is not None
    assert validated_rules(rules("9000", hit.chunk_id), [hit], FakeSession,
                           date(2026, 9, 17))[0] is None
    assert validated_rules(rules("7000", uuid4()), [hit], FakeSession,
                           date(2026, 9, 17))[0] is None


def test_gateway_unavailable_and_malformed_rule_output(monkeypatch):
    monkeypatch.setattr("app.gateway.model_gateway.settings.model_max_retries", 0)
    class Unavailable:
        async def generate_structured(self, **_kwargs):
            raise ConnectionError("provider down")
    class Malformed:
        async def generate_structured(self, *, model, **_kwargs):
            return ProviderResult(output={"rules": [{"rule_type": "AMOUNT_LIMIT"}]},
                                  provider="fake", model=model)
    async def invoke(provider):
        return await ModelGateway(provider).invoke_structured(
            task=ModelTask.EXPENSE_POLICY_RULE,
            messages=[{"role": "user", "content": "synthetic rule"}],
            output_schema=PolicyRuleSet, context=ModelContext(request_id="test"))
    with pytest.raises(ModelUnavailableError):
        asyncio.run(invoke(Unavailable()))
    with pytest.raises(StructuredOutputError):
        asyncio.run(invoke(Malformed()))
