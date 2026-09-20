"""Strict observability and evaluation contracts."""
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TraceErrorCategory(StrEnum):
    VALIDATION = "validation"
    RETRIEVAL = "retrieval"
    RERANKER = "reranker"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    MODEL_VALIDATION = "model_validation"
    MODEL_UNAVAILABLE = "model_unavailable"
    GUARDRAIL = "guardrail"
    CITATION = "citation"
    WORKFLOW_CONFLICT = "workflow_conflict"
    DATABASE = "database"
    UNKNOWN = "unknown"


class TraceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: str
    stage: str
    outcome: Literal["success", "failure", "marker"]
    duration_ms: float = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_category: TraceErrorCategory | None = None


class MetricThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    precision_at_5: float = Field(default=0.80, ge=0, le=1)
    recall_at_10: float = Field(default=0.90, ge=0, le=1)
    citation_correctness: float = Field(default=0.95, ge=0, le=1)
    decision_accuracy: float = Field(default=1.0, ge=0, le=1)


def categorize_error(error: BaseException) -> TraceErrorCategory:
    from sqlalchemy.exc import SQLAlchemyError
    from app.core.exceptions import (
        GuardrailViolationError, IdempotencyConflictError, ModelUnavailableError,
        ProviderRateLimitError, ProviderTimeoutError, RerankerUnavailableError,
        RetrievalUnavailableError, ReviewConflictError, StructuredOutputError,
    )
    if isinstance(error, (ValueError, TypeError)):
        return TraceErrorCategory.VALIDATION
    if isinstance(error, RetrievalUnavailableError):
        return TraceErrorCategory.RETRIEVAL
    if isinstance(error, RerankerUnavailableError):
        return TraceErrorCategory.RERANKER
    if isinstance(error, (TimeoutError, ProviderTimeoutError)):
        return TraceErrorCategory.TIMEOUT
    if isinstance(error, ProviderRateLimitError):
        return TraceErrorCategory.RATE_LIMIT
    if isinstance(error, StructuredOutputError):
        return TraceErrorCategory.MODEL_VALIDATION
    if isinstance(error, GuardrailViolationError):
        return TraceErrorCategory.GUARDRAIL
    if isinstance(error, ModelUnavailableError):
        return TraceErrorCategory.MODEL_UNAVAILABLE
    if isinstance(error, (IdempotencyConflictError, ReviewConflictError)):
        return TraceErrorCategory.WORKFLOW_CONFLICT
    if isinstance(error, SQLAlchemyError):
        return TraceErrorCategory.DATABASE
    return TraceErrorCategory.UNKNOWN
