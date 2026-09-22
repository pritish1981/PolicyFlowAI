"""Single governed provider-neutral structured invocation pipeline."""
import asyncio, inspect
from dataclasses import dataclass
from time import monotonic
from typing import TypeVar
from pydantic import BaseModel, ValidationError
from app.core.config import settings
from app.core.exceptions import (
    GatewayError, ModelUnavailableError, StructuredOutputValidationError, ProviderTimeoutError,
)
from app.gateway.models import GatewayResult, ModelUsage, ProviderRequest, EvidenceContext
from app.gateway.prompt_registry import prompt_for
from app.gateway.retry import is_transient_model_error, retry_delay
from app.gateway.routing import ModelTask, route_policy
from app.gateway.token_control import enforce_character_budget, consume_thread_budget
from app.guardrails.input_guard import validate_input
from app.guardrails.policy_guard import validate_evidence
from app.guardrails.output_guard import validate_output
from app.observability.tracing import emit_gateway_event
T=TypeVar("T",bound=BaseModel)

@dataclass(frozen=True)
class ModelContext:
    """Backward-compatible caller context accepted by the governed gateway."""
    request_id: str
    thread_id: str | None = None
    prompt_version: str = "policy-qa-v1"
    scenario: str | None = None
    metadata: dict[str, str] | None = None

class ModelGateway:
    def __init__(self,provider,fallback_provider=None,thread_budget_client=None):
        self.provider=provider; self.fallback_provider=fallback_provider; self.thread_budget_client=thread_budget_client
    async def _call(self,provider,request):
        if "request" in inspect.signature(provider.generate_structured).parameters:
            return await provider.generate_structured(request=request)
        return await provider.generate_structured(messages=request.messages,output_schema=request.output_schema,
            model=request.model,max_output_tokens=request.max_output_tokens)
    async def _transport(self,provider,request,retries):
        last=None
        for attempt in range(retries+1):
            try: return await asyncio.wait_for(self._call(provider,request),request.timeout_seconds),attempt
            except asyncio.TimeoutError as exc: last=ProviderTimeoutError("model provider timed out")
            except Exception as exc: last=exc
            if attempt>=retries or not is_transient_model_error(last): break
            await asyncio.sleep(retry_delay(attempt,settings.model_retry_base_delay_ms))
        if isinstance(last, (GatewayError, StructuredOutputValidationError)):
            raise last
        raise ModelUnavailableError("model provider is unavailable") from last
    async def invoke_structured(self,*,task:ModelTask,messages:list[dict[str,str]],output_schema:type[T],
            context:ModelContext,evidence:list[EvidenceContext]|None=None)->GatewayResult[T]:
        scenario = context.scenario or {
            ModelTask.POLICY_QA: "policy_qa",
            ModelTask.EXPENSE_POLICY_RULE: "expense_assessment",
            ModelTask.EXCEPTION_REVIEW_SUMMARY: "exception_review",
        }[task]
        policy=route_policy(task); prompt=prompt_for(task); guard=validate_input(messages,scenario,task)
        evidence=evidence or []; validate_evidence(evidence,settings.model_context_max_chunks,settings.model_context_max_chars)
        estimated=enforce_character_budget(messages,policy.max_input_tokens)
        consume_thread_budget(self.thread_budget_client,context.thread_id,estimated,settings.thread_token_budget,settings.thread_budget_ttl_seconds)
        started=monotonic(); validation_retries=0; fallback_used=False; total_retries=0; last=None
        providers=[(self.provider,policy.primary_model)]
        if self.fallback_provider and policy.fallback_model: providers.append((self.fallback_provider,policy.fallback_model))
        for index,(provider,model) in enumerate(providers):
            req=ProviderRequest(messages,output_schema,model,policy.max_output_tokens,policy.timeout_seconds)
            try:
                response,retries=await self._transport(provider,req,policy.max_retries); total_retries+=retries
                for repair in range(policy.repair_attempts+1):
                    try:
                        output=response.output if isinstance(response.output,output_schema) else output_schema.model_validate(response.output)
                        validate_output(task,output,{str(e.chunk_id) for e in evidence})
                        total=response.input_tokens+response.output_tokens if response.input_tokens is not None and response.output_tokens is not None else None
                        usage=ModelUsage(
                            provider=response.provider,
                            model=response.model,
                            latency_ms=int((monotonic()-started)*1000),
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                            retry_count=total_retries,
                            task=task.value,
                            prompt_version=prompt.version,
                            request_id=context.request_id,
                            thread_id=context.thread_id,
                            total_tokens=total,
                            validation_retry_count=validation_retries,
                            fallback_used=fallback_used,
                            guardrail_outcome=guard,
                        )
                        emit_gateway_event("model_gateway.succeeded", **usage.__dict__)
                        return GatewayResult(output,usage)
                    except (ValidationError,ValueError) as exc:
                        last=exc
                        if repair>=policy.repair_attempts: break
                        validation_retries+=1
                        repair_request=ProviderRequest(
                            messages=[*messages, {"role": "system", "content":
                                "Return one corrected response that exactly matches the registered output schema. "
                                "Do not add facts, evidence, citations, or authority."}],
                            output_schema=output_schema, model=model,
                            max_output_tokens=policy.max_output_tokens,
                            timeout_seconds=policy.timeout_seconds,
                        )
                        response,_=await self._transport(provider,repair_request,0)
                raise StructuredOutputValidationError("provider output failed governed validation") from last
            except ModelUnavailableError as exc:
                last=exc
                if index+1<len(providers): fallback_used=True; continue
                emit_gateway_event(
                    "model_gateway.failed", task=task.value,
                    prompt_version=prompt.version, request_id=context.request_id,
                    thread_id=context.thread_id, retry_count=total_retries,
                    fallback_used=fallback_used, guardrail_outcome=guard,
                    error_category=getattr(exc, "code", "MODEL_GATEWAY_ERROR"),
                )
                raise
        raise ModelUnavailableError("model provider is unavailable") from last
