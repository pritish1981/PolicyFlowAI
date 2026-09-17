"""Lazy OpenAI structured-output provider adapter."""
from pydantic import BaseModel

from app.gateway.providers.base import ProviderResult


class OpenAIProvider:
    def __init__(self, api_key: str, timeout: float) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.api_key = api_key
        self.timeout = timeout

    async def generate_structured(self, *, messages: list[dict[str, str]],
                                  output_schema: type[BaseModel], model: str,
                                  max_output_tokens: int) -> ProviderResult:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
        response = await client.responses.parse(
            model=model, input=messages, text_format=output_schema,
            max_output_tokens=max_output_tokens,
        )
        parsed = response.output_parsed
        usage = getattr(response, "usage", None)
        return ProviderResult(
            output=parsed, provider="openai", model=model,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
