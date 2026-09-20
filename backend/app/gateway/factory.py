"""Shared configured gateway construction."""
from functools import lru_cache
from app.cache.redis_client import redis_client
from app.core.config import settings
from app.core.exceptions import ModelUnavailableError
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.openai_provider import OpenAIProvider
class UnavailableProvider:
    async def generate_structured(self,**_kwargs): raise ModelUnavailableError("model provider is not configured")
@lru_cache(maxsize=1)
def get_model_gateway():
    primary=OpenAIProvider(settings.openai_api_key,settings.model_timeout_seconds) if settings.openai_api_key else UnavailableProvider()
    fallback=OpenAIProvider(settings.openai_api_key,settings.model_timeout_seconds) if settings.openai_api_key and settings.openai_fallback_model else None
    return ModelGateway(primary,fallback,redis_client)
