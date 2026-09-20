"""Use-case based model routing."""
from enum import StrEnum

from app.core.config import settings
from app.core.exceptions import UnsupportedModelTaskError
from app.gateway.models import ModelRoutePolicy


class ModelTask(StrEnum):
    POLICY_QA = "POLICY_QA"
    EXPENSE_POLICY_RULE = "EXPENSE_POLICY_RULE"
    EXCEPTION_REVIEW_SUMMARY = "EXCEPTION_REVIEW_SUMMARY"


def route_policy(task: ModelTask) -> ModelRoutePolicy:
    primary = settings.openai_primary_model or settings.openai_model
    values = {
        ModelTask.POLICY_QA: ("policy-qa-v1", settings.policy_qa_model or primary,
            settings.policy_qa_max_input_tokens, settings.policy_qa_max_output_tokens),
        ModelTask.EXPENSE_POLICY_RULE: ("expense-rule-v1", settings.expense_rule_model or primary,
            settings.expense_rule_max_input_tokens, settings.expense_rule_max_output_tokens),
        ModelTask.EXCEPTION_REVIEW_SUMMARY: ("exception-review-summary-v1",
            settings.exception_summary_model or primary, settings.exception_summary_max_input_tokens,
            settings.exception_summary_max_output_tokens),
    }
    try: version, model, input_limit, output_limit = values[task]
    except (KeyError, TypeError) as exc:
        raise UnsupportedModelTaskError("model task is not supported") from exc
    return ModelRoutePolicy(task=task.value, prompt_version=version, primary_model=model,
        fallback_model=settings.openai_fallback_model, max_input_tokens=input_limit,
        max_output_tokens=output_limit, timeout_seconds=settings.model_timeout_seconds,
        max_retries=settings.model_max_retries, repair_attempts=min(settings.model_validation_retries, 1))

def route_model(task: ModelTask) -> str:
    return route_policy(task).primary_model
