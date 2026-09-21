from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


def test_cloud_runtime_settings_parse_bounded_values() -> None:
    configured = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://user:pass@db:5432/policyflow",
        redis_url="rediss://cache:6379/0",
        cors_origins="https://app.example.test, https://admin.example.test",
        trusted_hosts="app.example.test,origin.example.test",
        enable_api_docs=False,
        database_pool_size=8,
        database_connect_timeout_seconds=7,
        redis_connect_timeout_seconds=2.5,
    )

    assert configured.allowed_origins == [
        "https://app.example.test",
        "https://admin.example.test",
    ]
    assert configured.allowed_hosts == ["app.example.test", "origin.example.test"]
    assert configured.enable_api_docs is False
    assert configured.database_pool_size == 8
    assert configured.database_connect_timeout_seconds == 7
    assert configured.redis_connect_timeout_seconds == 2.5


def test_liveness_does_not_require_external_dependencies() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_allows_alb_private_ip_host_but_api_rejects_it() -> None:
    client = TestClient(app, base_url="http://10.42.10.25:8000")

    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 400


def test_production_container_sources_do_not_embed_environment_files() -> None:
    root = Path(__file__).resolve().parents[2]
    backend_dockerfile = (root / "backend" / "Dockerfile").read_text(encoding="utf-8")
    frontend_dockerfile = (root / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "USER policyflow" in backend_dockerfile
    assert "COPY .env" not in backend_dockerfile
    assert "nginx-unprivileged" in frontend_dockerfile
    assert "COPY .env" not in frontend_dockerfile
