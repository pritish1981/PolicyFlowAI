"""Fail-open, exporter-neutral runtime tracing."""
from __future__ import annotations

import logging
import inspect
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Protocol
from uuid import UUID, uuid4

from app.core.config import settings
from app.observability.context import TraceContext
from app.observability.contracts import TraceRecord, categorize_error
from app.observability.redaction import sanitize_metadata

logger = logging.getLogger(__name__)


class TraceExporter(Protocol):
    def start(self, run_id: UUID, stage: str, metadata: dict[str, object],
              parent_run_id: UUID | None) -> None: ...
    def finish(self, run_id: UUID, record: TraceRecord) -> None: ...


class LangSmithExporter:
    """Small adapter around the declared LangSmith client API."""
    def __init__(self, api_key: str, endpoint: str, project: str) -> None:
        from langsmith import Client
        self.client = Client(api_key=api_key, api_url=endpoint)
        self.project = project

    def start(self, run_id: UUID, stage: str, metadata: dict[str, object],
              parent_run_id: UUID | None) -> None:
        kwargs = {"id": run_id, "parent_run_id": parent_run_id,
                  "project_name": self.project, "extra": {"metadata": metadata}}
        if parent_run_id is None:
            kwargs["trace_id"] = run_id
        self.client.create_run(stage, inputs={}, run_type="chain", **kwargs)

    def finish(self, run_id: UUID, record: TraceRecord) -> None:
        error = record.error_category.value if record.error_category else None
        self.client.update_run(run_id, outputs={"outcome": record.outcome}, error=error,
                               extra={"metadata": record.metadata,
                                      "duration_ms": record.duration_ms})


_exporter_override: ContextVar[TraceExporter | None] = ContextVar(
    "policyflow_trace_exporter", default=None)
_parent_run: ContextVar[UUID | None] = ContextVar("policyflow_parent_run", default=None)
_active_metadata: ContextVar[dict[str, object] | None] = ContextVar(
    "policyflow_active_trace_metadata", default=None)


def _configured_exporter() -> TraceExporter | None:
    override = _exporter_override.get()
    if override is not None:
        return override
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return None
    try:
        return LangSmithExporter(settings.langsmith_api_key, settings.langsmith_endpoint,
                                 settings.langsmith_project)
    except Exception:
        logger.warning("trace.exporter_unavailable", extra={"policyflow": {
            "event": "trace.exporter_unavailable", "error_category": "unknown"}})
        return None


@contextmanager
def use_exporter(exporter: TraceExporter | None) -> Iterator[None]:
    token = _exporter_override.set(exporter)
    try:
        yield
    finally:
        _exporter_override.reset(token)


@contextmanager
def stage_span(stage: str, context: TraceContext, **metadata: object) -> Iterator[None]:
    exporter = _configured_exporter()
    run_id, parent = uuid4(), _parent_run.get()
    safe = sanitize_metadata({**context.metadata(), "stage": stage, **metadata})
    started = time.perf_counter()
    if exporter:
        try:
            exporter.start(run_id, stage, safe, parent)
        except Exception:
            logger.warning("trace.export_failed", extra={"policyflow": {
                "event": "trace.export_failed", "stage": stage,
                "request_id": context.request_id, "error_category": "unknown"}})
    token = _parent_run.set(run_id)
    metadata_token = _active_metadata.set(safe)
    try:
        yield
    except Exception as error:
        _finish(exporter, run_id, stage, safe, started, "failure", categorize_error(error))
        raise
    else:
        _finish(exporter, run_id, stage, safe, started, "success", None)
    finally:
        _active_metadata.reset(metadata_token)
        _parent_run.reset(token)


def annotate_span(**metadata: object) -> None:
    active = _active_metadata.get()
    if active is not None:
        active.update(sanitize_metadata(metadata))


def traced_node(stage: str, function):
    """Wrap a LangGraph node without serializing its state or changing its result."""
    if inspect.iscoroutinefunction(function):
        async def async_wrapper(state):
            with stage_span(stage, TraceContext.from_state(state)):
                return await function(state)
        return async_wrapper

    def wrapper(state):
        with stage_span(stage, TraceContext.from_state(state)):
            return function(state)
    return wrapper


def _finish(exporter: TraceExporter | None, run_id: UUID, stage: str,
            metadata: dict[str, object], started: float, outcome: str, error_category) -> None:
    record = TraceRecord(event="stage.completed", stage=stage, outcome=outcome,
                         duration_ms=max(0, (time.perf_counter() - started) * 1000),
                         metadata=metadata, error_category=error_category)
    logger.info("trace.stage", extra={"policyflow": sanitize_metadata({
        "event": record.event, "stage": stage, "outcome": outcome,
        "duration_ms": record.duration_ms, "error_category": error_category, **metadata})})
    if exporter:
        try:
            exporter.finish(run_id, record)
        except Exception:
            logger.warning("trace.export_failed", extra={"policyflow": {
                "event": "trace.export_failed", "stage": stage,
                "error_category": "unknown"}})


def emit_marker(event: str, context: TraceContext, **metadata: object) -> None:
    safe = sanitize_metadata({"event": event, "stage": event, "outcome": "marker",
                              **context.metadata(), **metadata})
    logger.info(event, extra={"policyflow": safe})
    exporter = _configured_exporter()
    if exporter:
        run_id = uuid4()
        try:
            exporter.start(run_id, event, safe, _parent_run.get())
            exporter.finish(run_id, TraceRecord(event=event, stage=event, outcome="marker",
                                                duration_ms=0, metadata=safe))
        except Exception:
            logger.warning("trace.export_failed", extra={"policyflow": {
                "event": "trace.export_failed", "stage": event,
                "error_category": "unknown"}})


def emit_gateway_event(event: str, **fields: object) -> None:
    """Preserve Phase 006 telemetry while routing through the shared facade."""
    request_id = str(fields.get("request_id") or "unknown")
    context = TraceContext(request_id, str(fields.get("thread_id") or request_id),
                           str(fields.get("scenario") or "model_gateway"))
    emit_marker(event, context, **fields)
