"""Thin Policy Q&A HTTP adapter."""
from functools import lru_cache
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import settings
from app.core.exceptions import (
    ModelUnavailableError, RerankerUnavailableError, RetrievalUnavailableError,
    StructuredOutputError,
)
from app.db.session import SessionLocal
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.openai_provider import OpenAIProvider
from app.graph.graph import PolicyQADependencies
from app.schemas.policy import PolicyAnswerResponse, PolicyQueryRequest
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/api/v1/policy", tags=["policy"])


@lru_cache(maxsize=1)
def get_policy_service() -> PolicyService:
    if not settings.openai_api_key:
        raise ModelUnavailableError("OPENAI_API_KEY is not configured")
    gateway = ModelGateway(OpenAIProvider(settings.openai_api_key,
                                          settings.model_timeout_seconds))
    return PolicyService(PolicyQADependencies(session_factory=SessionLocal, gateway=gateway))


@router.post("/query", response_model=PolicyAnswerResponse)
async def query_policy(request: PolicyQueryRequest,
                       x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
                       service: PolicyService = Depends(get_policy_service)) -> PolicyAnswerResponse:
    request_id = x_request_id.strip() if x_request_id and x_request_id.strip() else str(uuid4())
    try:
        return await service.query(request, request_id=request_id)
    except (ModelUnavailableError, RerankerUnavailableError,
            RetrievalUnavailableError, StructuredOutputError) as exc:
        raise HTTPException(status_code=503, detail={
            "code": exc.code, "message": "Policy Q&A is temporarily unavailable.",
            "request_id": request_id, "retryable": exc.retryable,
        }) from exc
