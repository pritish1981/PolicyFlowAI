import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import engine
from app.cache.redis_client import redis_client

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "policyflow-api",
    }


@router.get("/ready")
def ready() -> JSONResponse:
    components = {"postgresql": "down", "redis": "down"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        components["postgresql"] = "ready"
    except Exception:
        logger.warning("PostgreSQL readiness check failed")
    try:
        if redis_client.ping():
            components["redis"] = "ready"
    except Exception:
        logger.warning("Redis readiness check failed")
    healthy = all(value == "ready" for value in components.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "unavailable", "components": components},
    )
