from fastapi import APIRouter, Response, status

from app.cache.redis_client import check_redis
from app.db.health import check_database


router = APIRouter(tags=["readiness"])


@router.get("/ready")
def readiness(response: Response):
    postgres_ok = check_database()
    redis_ok = check_redis()

    ready = postgres_ok and redis_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if ready else "not_ready",
        "dependencies": {
            "postgres": "up" if postgres_ok else "down",
            "redis": "up" if redis_ok else "down",
        },
    }