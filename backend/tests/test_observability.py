"""Phase 007 privacy-safe tracing tests; no network is used."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.exceptions import (
    GuardrailViolationError, ProviderRateLimitError, RetrievalUnavailableError,
    ReviewConflictError, StructuredOutputError,
)
from app.observability.context import TraceContext
from app.observability.contracts import (
    MetricThresholds, TraceErrorCategory, TraceRecord, categorize_error,
)
from app.observability.metrics import citation_metadata, decision_metadata
from app.observability.redaction import MAX_LIST, MAX_STRING, sanitize_metadata
from app.observability.tracing import emit_gateway_event, stage_span, use_exporter


class RecordingExporter:
    def __init__(self, fail=False):
        self.started, self.finished, self.fail = [], [], fail

    def start(self, run_id, stage, metadata, parent_run_id):
        if self.fail:
            raise RuntimeError("offline")
        self.started.append((run_id, stage, metadata, parent_run_id))

    def finish(self, run_id, record):
        if self.fail:
            raise RuntimeError("offline")
        self.finished.append((run_id, record))


def test_phase_007_configuration_defaults_and_overrides():
    base = dict(database_url="postgresql+psycopg://x:x@localhost/x",
                redis_url="redis://localhost:6379/0")
    configured = Settings(_env_file=None, **base)
    assert configured.langsmith_tracing is False
    assert configured.langsmith_api_key is None
    assert configured.enable_ai_evaluation is False
    assert configured.evaluation_precision_at_5_threshold == .8
    overridden = Settings(_env_file=None, **base, langsmith_tracing=True,
                          evaluation_recall_at_10_threshold=.93)
    assert overridden.langsmith_tracing is True
    assert overridden.evaluation_recall_at_10_threshold == .93
    assert overridden.langsmith_api_key is None


def test_context_is_immutable_and_preserves_existing_ids():
    context = TraceContext("request", "thread", "policy_qa", expense_id="expense")
    assert context.metadata() == {"request_id": "request", "thread_id": "thread",
                                  "scenario": "policy_qa", "expense_id": "expense"}
    with pytest.raises(FrozenInstanceError):
        context.request_id = "different"
    derived = TraceContext.from_state(context.metadata())
    assert derived.request_id == "request" and derived.thread_id == "thread"


def test_recursive_redaction_and_bounds():
    safe = sanitize_metadata({
        "request_id": "r", "prompt_version": "policy-qa-v2",
        "metadata_filters": {"category": "HOTEL", "authorization": "Bearer secret"},
        "selected_chunk_ids": [str(index) for index in range(MAX_LIST + 5)],
        "purpose": "employee medical details", "raw_provider_payload": {"x": "secret"},
        "api_key": "secret", "comments": "never export", "policy_body": "never export",
        "stage": "x" * (MAX_STRING + 10),
    })
    serialized = json.dumps(safe)
    assert safe["request_id"] == "r"
    assert safe["prompt_version"] == "policy-qa-v2"
    assert safe["metadata_filters"] == {"category": "HOTEL"}
    assert len(safe["selected_chunk_ids"]) == MAX_LIST
    assert len(safe["stage"]) == MAX_STRING
    assert "secret" not in serialized and "medical" not in serialized


@pytest.mark.parametrize("error,category", [
    (ValueError(), TraceErrorCategory.VALIDATION),
    (RetrievalUnavailableError(), TraceErrorCategory.RETRIEVAL),
    (ProviderRateLimitError(), TraceErrorCategory.RATE_LIMIT),
    (StructuredOutputError(), TraceErrorCategory.MODEL_VALIDATION),
    (GuardrailViolationError(), TraceErrorCategory.GUARDRAIL),
    (ReviewConflictError(), TraceErrorCategory.WORKFLOW_CONFLICT),
    (RuntimeError(), TraceErrorCategory.UNKNOWN),
])
def test_error_categories(error, category):
    assert categorize_error(error) == category


def test_trace_contracts_are_strict_and_serializable():
    record = TraceRecord(event="done", stage="retrieve", outcome="success",
                         duration_ms=1.25, metadata={"count": 1})
    assert TraceRecord.model_validate_json(record.model_dump_json()) == record
    with pytest.raises(ValidationError):
        TraceRecord(event="done", stage="x", outcome="success", duration_ms=0, extra=True)
    with pytest.raises(ValidationError):
        MetricThresholds(precision_at_5=1.1)


def test_stage_spans_have_hierarchy_and_fail_open(monkeypatch):
    exporter = RecordingExporter()
    context = TraceContext("request", "thread", "policy_qa")
    with use_exporter(exporter):
        with stage_span("root", context):
            with stage_span("child", context, count=2):
                pass
    assert [item[1] for item in exporter.started] == ["root", "child"]
    assert exporter.started[0][3] is None
    assert exporter.started[1][3] == exporter.started[0][0]
    assert all(item[1].duration_ms >= 0 for item in exporter.finished)

    with use_exporter(RecordingExporter(fail=True)):
        with stage_span("business", context):
            result = "unchanged"
    assert result == "unchanged"

    with use_exporter(exporter):
        with pytest.raises(ValueError, match="domain error"):
            with stage_span("failure", context):
                raise ValueError("domain error")
    assert exporter.finished[-1][1].error_category == TraceErrorCategory.VALIDATION


def test_contextvars_isolate_concurrent_requests():
    def execute(identifier):
        exporter = RecordingExporter()
        with use_exporter(exporter):
            with stage_span("request", TraceContext(identifier, identifier, "policy_qa")):
                pass
        return exporter.started[0][2]["request_id"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert set(pool.map(execute, ["a", "b"])) == {"a", "b"}


def test_gateway_event_creates_one_governed_export_without_payload():
    exporter = RecordingExporter()
    with use_exporter(exporter):
        emit_gateway_event(
            "model_gateway.succeeded", request_id="request", thread_id="thread",
            task="POLICY_QA", provider="fake", model="fake-model",
            prompt_version="policy-qa-v2", input_tokens=12, output_tokens=4,
            retry_count=0, fallback_used=False, raw_provider_payload="SECRET")
    assert len(exporter.started) == len(exporter.finished) == 1
    metadata = exporter.started[0][2]
    assert metadata["task"] == "POLICY_QA"
    assert metadata["prompt_version"] == "policy-qa-v2"
    assert "raw_provider_payload" not in metadata


def test_metric_builders_exclude_free_text():
    decision = decision_metadata(expense_type="HOTEL", rule_type="AMOUNT_LIMIT",
                                 policy_limit=Decimal("7000"), decision="COMPLIANT",
                                 confidence=Decimal("1"), citation_count=2)
    assert decision["policy_limit"] == "7000"
    citations = citation_metadata([uuid4(), uuid4()], [])
    assert citations["generated_count"] == 2 and citations["invalid_count"] == 2
    assert "purpose" not in json.dumps({**decision, **citations})
