"""Deterministic request guardrails; never business decision logic."""
import re
from app.core.exceptions import GuardrailViolationError
from app.gateway.routing import ModelTask

_INJECTION = re.compile(r"ignore (?:all |the )?(?:previous|prior) instructions|reveal (?:the )?system prompt|do not follow policy evidence|override policy", re.I)

_SCENARIOS = {
    ModelTask.POLICY_QA: "policy_qa",
    ModelTask.EXPENSE_POLICY_RULE: "expense_assessment",
    ModelTask.EXCEPTION_REVIEW_SUMMARY: "exception_review",
}


def validate_input(messages: list[dict[str, str]], scenario: str, task: ModelTask) -> str:
    if not scenario or not messages or any(m.get("role") not in {"system", "user", "assistant"} or not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
        raise GuardrailViolationError("model input is empty or malformed")
    if _SCENARIOS.get(task) != scenario:
        raise GuardrailViolationError("model task is not valid for the requested scenario")
    user_text = "\n".join(m["content"] for m in messages if m["role"] == "user")
    if _INJECTION.search(user_text):
        raise GuardrailViolationError("model input violated instruction-boundary controls")
    return "PASSED"
