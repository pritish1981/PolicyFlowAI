"""Expense assessment HTTP adapter."""
import logging
from functools import lru_cache
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import Error as PsycopgError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (IdempotencyConflictError, ModelUnavailableError,
                                 RetrievalUnavailableError, RerankerUnavailableError,
                                 StructuredOutputError)
from app.db.session import SessionLocal
from app.gateway.model_gateway import ModelGateway
from app.gateway.providers.openai_provider import OpenAIProvider
from app.graph.expense_graph import ExpenseDependencies
from app.schemas.expense import ExpenseAssessmentResponse, ExpenseClarification, ExpenseCreate
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_expense_service() -> ExpenseService:
    if settings.openai_api_key:
        provider = OpenAIProvider(settings.openai_api_key, settings.model_timeout_seconds)
    else:
        class UnavailableProvider:
            async def generate_structured(self, **_kwargs):
                raise ModelUnavailableError("OPENAI_API_KEY is not configured")
        provider = UnavailableProvider()
    gateway = ModelGateway(provider)
    return ExpenseService(ExpenseDependencies(SessionLocal, gateway), settings.database_url)


def _failure(exc: Exception, request_id: str) -> HTTPException:
    logger.warning("expense assessment unavailable", extra={"request_id": request_id,
                   "error_type": type(exc).__name__})
    return HTTPException(503, detail={"code": getattr(exc, "code", "ASSESSMENT_UNAVAILABLE"),
                        "message": "Expense assessment is temporarily unavailable.",
                        "request_id": request_id, "retryable": True})


@router.post("", response_model=ExpenseAssessmentResponse)
async def create_expense(request: ExpenseCreate,
                         x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
                         idempotency_key: str | None = Header(default=None, alias="Idempotency-Key",
                                                              min_length=1, max_length=200),
                         service: ExpenseService = Depends(get_expense_service)):
    request_id = x_request_id.strip() if x_request_id and x_request_id.strip() else str(uuid4())
    try:
        return await service.create(request, request_id, idempotency_key)
    except IdempotencyConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except (ModelUnavailableError, RetrievalUnavailableError, RerankerUnavailableError,
            StructuredOutputError, SQLAlchemyError, PsycopgError, OSError) as exc:
        raise _failure(exc, request_id) from exc


@router.post("/{expense_id}/clarifications", response_model=ExpenseAssessmentResponse)
async def clarify_expense(expense_id: UUID, request: ExpenseClarification,
                          service: ExpenseService = Depends(get_expense_service)):
    try:
        result = await service.clarify(expense_id, request)
        if result is None:
            raise HTTPException(404, detail="Expense not found")
        return result
    except IdempotencyConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except (ModelUnavailableError, RetrievalUnavailableError, RerankerUnavailableError,
            StructuredOutputError, SQLAlchemyError, PsycopgError, OSError) as exc:
        raise _failure(exc, str(expense_id)) from exc
