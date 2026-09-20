"""Use-case based model routing."""
from enum import StrEnum

from app.core.config import settings


class ModelTask(StrEnum):
    POLICY_QA = "POLICY_QA"
    EXPENSE_POLICY_RULE = "EXPENSE_POLICY_RULE"
    EXCEPTION_REVIEW_SUMMARY = "EXCEPTION_REVIEW_SUMMARY"


def route_model(task: ModelTask) -> str:
    if task not in (ModelTask.POLICY_QA, ModelTask.EXPENSE_POLICY_RULE,
                    ModelTask.EXCEPTION_REVIEW_SUMMARY):
        raise ValueError(f"unsupported model task: {task}")
    return settings.openai_model
