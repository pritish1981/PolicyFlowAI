"""Human review HTTP adapters."""
from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import demo_employee, demo_reviewer
from app.core.config import settings
from app.core.exceptions import ModelUnavailableError, ReviewConflictError
from app.db.session import SessionLocal
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.openai_provider import OpenAIProvider
from app.schemas.review import (
    ExceptionInformation,
    ExceptionOutcome,
    ReviewAction,
    ReviewDetail,
    ReviewListItem,
)
from app.services.exception_service import ExceptionService

router = APIRouter(prefix="/api/v1", tags=["exception-review"])


@lru_cache(maxsize=1)
def get_exception_service() -> ExceptionService:
    if settings.openai_api_key:
        provider = OpenAIProvider(settings.openai_api_key, settings.model_timeout_seconds)
    else:
        class UnavailableProvider:
            async def generate_structured(self, **_kwargs):
                raise ModelUnavailableError("OPENAI_API_KEY is not configured")
        provider = UnavailableProvider()
    return ExceptionService(SessionLocal, ModelGateway(provider), settings.database_url)


@router.get("/reviews/pending", response_model=list[ReviewListItem])
def pending_reviews(_reviewer: str = Depends(demo_reviewer),
                    service: ExceptionService = Depends(get_exception_service)):
    return service.pending()


@router.get("/reviews/{exception_id}", response_model=ReviewDetail)
def review_detail(exception_id: UUID, _reviewer: str = Depends(demo_reviewer),
                  service: ExceptionService = Depends(get_exception_service)):
    result = service.detail(exception_id)
    if result is None:
        raise HTTPException(404, detail="Exception not found")
    return result


@router.post("/reviews/{exception_id}/decision", response_model=ExceptionOutcome)
async def decide(exception_id: UUID, request: ReviewAction,
                 reviewer: str = Depends(demo_reviewer),
                 service: ExceptionService = Depends(get_exception_service)):
    try:
        return await service.decide(exception_id, reviewer, request)
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ReviewConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.post("/exceptions/{exception_id}/information", response_model=ExceptionOutcome)
async def add_information(exception_id: UUID, request: ExceptionInformation,
                          _employee: str = Depends(demo_employee),
                          service: ExceptionService = Depends(get_exception_service)):
    try:
        return await service.information(exception_id, request.information)
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ReviewConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
