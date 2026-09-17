"""Provider-neutral structured generation contracts."""
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel


@dataclass(frozen=True)
class ProviderResult:
    output: BaseModel | dict[str, Any]
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ProviderAdapter(Protocol):
    async def generate_structured(
        self, *, messages: list[dict[str, str]], output_schema: type[BaseModel],
        model: str, max_output_tokens: int,
    ) -> ProviderResult: ...
