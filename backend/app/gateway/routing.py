"""Use-case based model routing."""
from enum import StrEnum

from app.core.config import settings


class ModelTask(StrEnum):
    POLICY_QA = "POLICY_QA"


def route_model(task: ModelTask) -> str:
    if task != ModelTask.POLICY_QA:
        raise ValueError(f"unsupported model task: {task}")
    return settings.openai_model
