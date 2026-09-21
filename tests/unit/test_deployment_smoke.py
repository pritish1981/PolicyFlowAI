import pytest

from scripts import deployment_smoke


def test_deployment_smoke_accepts_healthy_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(deployment_smoke, "fetch_text", lambda *_: (200, "<html></html>"))
    responses = iter(
        [
            (200, {"status": "ok"}),
            (
                200,
                {
                    "status": "ready",
                    "components": {"postgresql": "ready", "redis": "ready"},
                },
            ),
        ]
    )
    monkeypatch.setattr(deployment_smoke, "fetch_json", lambda *_: next(responses))

    result = deployment_smoke.run("https://policyflow.example.test", 1)

    assert result == {
        "status": "passed",
        "frontend": 200,
        "health": 200,
        "readiness": 200,
    }


def test_deployment_smoke_rejects_unready_backend(monkeypatch) -> None:
    monkeypatch.setattr(deployment_smoke, "fetch_text", lambda *_: (200, "<html></html>"))
    responses = iter(
        [
            (200, {"status": "ok"}),
            (503, {"status": "unavailable"}),
        ]
    )
    monkeypatch.setattr(deployment_smoke, "fetch_json", lambda *_: next(responses))

    with pytest.raises(RuntimeError, match="readiness failed"):
        deployment_smoke.run("https://policyflow.example.test", 1)
