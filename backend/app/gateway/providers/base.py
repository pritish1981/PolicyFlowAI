"""Provider-neutral structured generation contracts."""
from typing import Protocol
from app.gateway.models import ProviderRequest, ProviderResponse

ProviderResult = ProviderResponse


class ProviderAdapter(Protocol):
    async def generate_structured(
        self, request: ProviderRequest,
    ) -> ProviderResponse: ...
