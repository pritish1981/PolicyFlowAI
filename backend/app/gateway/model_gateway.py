"""Governed provider-neutral structured model invocation."""
import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import ModelUnavailableError, StructuredOutputError
from app.gateway.providers.base import ProviderAdapter
from app.gateway.retry import is_transient_model_error
from app.gateway.routing import ModelTask, route_model
from app.gateway.token_control import enforce_character_budget

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class ModelContext:
    request_id: str
    thread_id: str | None = None
    prompt_version: str = "policy-qa-v1"


@dataclass(frozen=True)
class ModelUsage:
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    retry_count: int = 0


@dataclass(frozen=True)
class GatewayResult(Generic[T]):
    output: T
    usage: ModelUsage


class ModelGateway:
    def __init__(self, provider: ProviderAdapter) -> None:
        self.provider = provider

    async def invoke_structured(self, *, task: ModelTask,
                                messages: list[dict[str, str]],
                                output_schema: type[T], context: ModelContext) -> GatewayResult[T]:
        del context  # correlation remains with the caller's sanitized logs
        enforce_character_budget(messages, settings.thread_token_budget)
        model = route_model(task)
        started = monotonic()
        last_error: Exception | None = None
        for attempt in range(settings.model_max_retries + 1):
            try:
                provider_result = await asyncio.wait_for(
                    self.provider.generate_structured(
                        messages=messages, output_schema=output_schema, model=model,
                        max_output_tokens=settings.max_output_tokens,
                    ), timeout=settings.model_timeout_seconds,
                )
                try:
                    output = (provider_result.output if isinstance(provider_result.output, output_schema)
                              else output_schema.model_validate(provider_result.output))
                except ValidationError as exc:
                    last_error = exc
                    if attempt < min(settings.model_max_retries, 1):
                        continue
                    raise StructuredOutputError("provider output failed schema validation") from exc
                return GatewayResult(output=output, usage=ModelUsage(
                    provider=provider_result.provider, model=provider_result.model,
                    latency_ms=int((monotonic() - started) * 1000),
                    input_tokens=provider_result.input_tokens,
                    output_tokens=provider_result.output_tokens, retry_count=attempt,
                ))
            except StructuredOutputError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= settings.model_max_retries or not is_transient_model_error(exc):
                    break
                await asyncio.sleep(min(0.1 * (2 ** attempt), 0.5))
        raise ModelUnavailableError("model provider is unavailable") from last_error
