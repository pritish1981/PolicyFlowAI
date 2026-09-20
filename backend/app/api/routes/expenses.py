"""Expense assessment HTTP adapter."""
import logging
from functools import lru_cache
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from psycopg import Error as PsycopgError
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import demo_employee
from app.api.routes.reviews import get_exception_service
from app.core.config import settings
from app.core.exceptions import (
    ExceptionIneligibleError,
    IdempotencyConflictError,
    ModelUnavailableError,
    RerankerUnavailableError,
    RetrievalUnavailableError,
    ReviewConflictError,
    StructuredOutputError,
)
from app.db.session import SessionLocal
from app.gateway.factory import get_model_gateway
from app.graph.expense_graph import ExpenseDependencies
from app.schemas.expense import ExpenseAssessmentResponse, ExpenseClarification, ExpenseCreate
from app.schemas.review import ExceptionCreate, ExceptionOutcome
from app.services.exception_service import ExceptionService
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_expense_service() -> ExpenseService:
    gateway = get_model_gateway()
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


@router.post("/{expense_id}/exceptions", response_model=ExceptionOutcome, status_code=201)
async def submit_exception(expense_id: UUID, request: ExceptionCreate,
                           response: Response,
                           _employee: str = Depends(demo_employee),
                           service: ExceptionService = Depends(get_exception_service)):
    try:
        result, created = await service.submit(expense_id, request.justification)
        if not created:
            response.status_code = 200
            return result
        return result
    except LookupError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except (ExceptionIneligibleError, ReviewConflictError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.get("/{expense_id}", response_model=ExpenseAssessmentResponse)
def get_expense(expense_id: UUID, service: ExpenseService = Depends(get_expense_service)):
    result = service.get(expense_id)
    if result is None:
        raise HTTPException(404, detail="Expense not found")
    return result
