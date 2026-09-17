from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine

from app.main import app


def test_readiness() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.exists():
        pytest.skip("Local .env is required for the live readiness test")

    values = dotenv_values(env_file)
    database_url = values.get("DATABASE_URL")
    redis_url = values.get("REDIS_URL")
    if not database_url or not redis_url:
        pytest.skip("Local database and Redis URLs are required")

    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    redis_client = Redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
    try:
        with patch("app.api.routes.health.engine", engine), patch(
            "app.api.routes.health.redis_client", redis_client
        ):
            response = TestClient(app).get("/ready")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "components": {"postgresql": "ready", "redis": "ready"},
        }
    finally:
        redis_client.close()
        engine.dispose()
