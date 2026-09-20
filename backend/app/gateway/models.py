"""Strict provider-neutral Model Gateway contracts."""
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)

class GatewayContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str = Field(min_length=1, max_length=200)
    thread_id: str | None = Field(default=None, max_length=200)
    scenario: str = Field(default="policy_qa", min_length=1, max_length=100)
    metadata: dict[str, str] = Field(default_factory=dict)

class EvidenceContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chunk_id: str = Field(min_length=1, max_length=100)
    policy_code: str = Field(min_length=1, max_length=100)
    policy_version: str = Field(min_length=1, max_length=100)
    section_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    status: str = "ACTIVE"
    eligible: bool = True
    approved_corpus: bool = True

@dataclass(frozen=True)
class ProviderRequest:
    messages: list[dict[str, str]]
    output_schema: type[BaseModel]
    model: str
    max_output_tokens: int
    timeout_seconds: float

@dataclass(frozen=True)
class ProviderResponse:
    output: BaseModel | dict[str, Any]
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None

@dataclass(frozen=True)
class ModelRoutePolicy:
    task: str
    prompt_version: str
    primary_model: str
    fallback_model: str | None
    max_input_tokens: int
    max_output_tokens: int
    timeout_seconds: float
    max_retries: int
    repair_attempts: int = 1
    fallback_eligible: bool = True

@dataclass(frozen=True)
class ModelUsage:
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    retry_count: int = 0
    task: str = "unknown"
    prompt_version: str = "unknown"
    request_id: str = "unknown"
    thread_id: str | None = None
    total_tokens: int | None = None
    validation_retry_count: int = 0
    fallback_used: bool = False
    guardrail_outcome: str = "PASSED"
    error_category: str | None = None

@dataclass(frozen=True)
class GatewayResult(Generic[T]):
    output: T
    usage: ModelUsage
