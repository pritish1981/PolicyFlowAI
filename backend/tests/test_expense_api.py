"""Public expense HTTP validation and failure mapping."""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.expenses import get_expense_service
from app.core.exceptions import ModelUnavailableError
from app.core.exceptions import IdempotencyConflictError
from app.main import app
from app.schemas.expense import Decision, ExpenseAssessmentResponse


class FakeService:
    def __init__(self):
        self.calls = []

    async def create(self, request, request_id, key):
        self.calls.append((request, request_id, key))
        return ExpenseAssessmentResponse(
            expense_id=uuid4(), thread_id="thread-1", request_id=request_id,
            decision=Decision.INSUFFICIENT_INFORMATION, confidence=0,
            explanation="Complete the missing fields.",
            next_action="PROVIDE_CLARIFICATION", missing_fields=request.missing_fields())

    async def clarify(self, expense_id, request):
        self.calls.append((expense_id, request))
        return ExpenseAssessmentResponse(
            expense_id=expense_id, thread_id="thread-1", request_id="request-1",
            decision=Decision.COMPLIANT, policy_limit="7000", confidence=1,
            explanation="Within cited limit.")


def test_expense_openapi_validation_and_clarification():
    fake = FakeService()
    app.dependency_overrides[get_expense_service] = lambda: fake
    try:
        with TestClient(app) as client:
            schema = client.get("/openapi.json").json()
            assert "/api/v1/expenses" in schema["paths"]
            assert "/api/v1/expenses/{expense_id}/clarifications" in schema["paths"]
            assert client.post("/api/v1/expenses", json={"amount": "-2"}).status_code == 422
            response = client.post("/api/v1/expenses", json={"expense_type": "HOTEL"},
                                   headers={"Idempotency-Key": "key-1", "X-Request-ID": "request-1"})
            assert response.status_code == 200
            body = response.json()
            assert body["decision"] == "INSUFFICIENT_INFORMATION"
            assert "amount" in body["missing_fields"]
            assert fake.calls[0][2] == "key-1"
            result = client.post(f"/api/v1/expenses/{body['expense_id']}/clarifications",
                                 json={"amount": "6500"})
            assert result.status_code == 200
            assert result.json()["decision"] == "COMPLIANT"
    finally:
        app.dependency_overrides.clear()


def test_provider_outage_is_sanitized_503():
    class Down:
        async def create(self, *_args):
            raise ModelUnavailableError("secret provider detail")

    app.dependency_overrides[get_expense_service] = lambda: Down()
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/expenses", json={},
                                   headers={"X-Request-ID": "outage-1"})
            assert response.status_code == 503
            assert response.json()["detail"]["request_id"] == "outage-1"
            assert "secret" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_conflicting_idempotency_key_is_409():
    class Conflict:
        async def create(self, *_args):
            raise IdempotencyConflictError("Key is bound to a different payload")

    app.dependency_overrides[get_expense_service] = lambda: Conflict()
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/expenses", json={},
                                   headers={"Idempotency-Key": "reused"})
            assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
