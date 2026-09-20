"""Lazy OpenAI structured-output provider adapter."""
from pydantic import BaseModel

from app.gateway.models import ProviderRequest, ProviderResponse
from app.core.exceptions import (
    GatewayError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenAIProvider:
    def __init__(self, api_key: str, timeout: float) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.api_key = api_key
        self.timeout = timeout

    async def generate_structured(
        self,
        request: ProviderRequest | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        output_schema: type[BaseModel] | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
    ) -> ProviderResponse:
        # Keyword arguments remain supported for the established adapter boundary.
        if request is None:
            if messages is None or output_schema is None or model is None or max_output_tokens is None:
                raise TypeError("a ProviderRequest or all legacy structured-call arguments are required")
            request = ProviderRequest(
                messages=messages,
                output_schema=output_schema,
                model=model,
                max_output_tokens=max_output_tokens,
                timeout_seconds=self.timeout,
            )
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, timeout=request.timeout_seconds)
        try:
            response = await client.responses.parse(
                model=request.model, input=request.messages, text_format=request.output_schema,
                max_output_tokens=request.max_output_tokens,
            )
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            name = type(exc).__name__.lower()
            if status == 429 or "ratelimit" in name:
                raise ProviderRateLimitError("model provider rate limit exceeded") from exc
            if "timeout" in name:
                raise ProviderTimeoutError("model provider timed out") from exc
            if "connection" in name or (isinstance(status, int) and status >= 500):
                raise ProviderUnavailableError("model provider is unavailable") from exc
            raise GatewayError("model provider request failed") from exc
        parsed = response.output_parsed
        usage = getattr(response, "usage", None)
        return ProviderResponse(
            output=parsed, provider="openai", model=request.model,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
