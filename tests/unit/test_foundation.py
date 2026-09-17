import json
import logging
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging import JsonFormatter
from app.main import app
from app.api.dependencies import get_db


client = TestClient(app)


def test_health_is_live_without_dependency_checks() -> None:
    with patch("app.api.routes.health.engine.connect") as connect:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "policyflow-api"}
        connect.assert_not_called()


def test_ready_when_both_dependencies_respond() -> None:
    with patch("app.api.routes.health.engine.connect") as connect, patch(
        "app.api.routes.health.redis_client.ping", return_value=True
    ):
        connect.return_value.__enter__.return_value.execute.return_value = 1
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["components"] == {"postgresql": "ready", "redis": "ready"}


def test_ready_degrades_without_disclosing_exception() -> None:
    with patch("app.api.routes.health.engine.connect", side_effect=RuntimeError("secret")), patch(
        "app.api.routes.health.redis_client.ping", return_value=True
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["components"] == {"postgresql": "down", "redis": "ready"}
    assert "secret" not in response.text


def test_local_cors() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_settings_require_connection_urls() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://example:example@localhost/db",
        redis_url="redis://localhost:6379/0",
        cors_origins="http://localhost:5173, http://127.0.0.1:5173",
    )
    assert len(settings.allowed_origins) == 2
    with patch.dict(os.environ, {}, clear=True), pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_json_log_shape() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert "timestamp" in payload


def test_session_dependency_closes_session() -> None:
    with patch("app.api.dependencies.SessionLocal") as factory:
        dependency = get_db()
        assert next(dependency) is factory.return_value
        try:
            next(dependency)
        except StopIteration:
            pass
        factory.return_value.close.assert_called_once()
