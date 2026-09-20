"""Central prompt and version registry."""
from dataclasses import dataclass
from app.core.exceptions import UnsupportedModelTaskError
from app.gateway.prompts import (POLICY_QA_SYSTEM_PROMPT, POLICY_QA_PROMPT_VERSION,
    EXPENSE_RULE_SYSTEM_PROMPT, EXPENSE_RULE_PROMPT_VERSION,
    EXCEPTION_SUMMARY_SYSTEM_PROMPT, EXCEPTION_SUMMARY_PROMPT_VERSION)
from app.gateway.routing import ModelTask

@dataclass(frozen=True)
class PromptContract:
    version: str
    system_prompt: str

_PROMPTS = {
    ModelTask.POLICY_QA: PromptContract(POLICY_QA_PROMPT_VERSION, POLICY_QA_SYSTEM_PROMPT),
    ModelTask.EXPENSE_POLICY_RULE: PromptContract(EXPENSE_RULE_PROMPT_VERSION, EXPENSE_RULE_SYSTEM_PROMPT),
    ModelTask.EXCEPTION_REVIEW_SUMMARY: PromptContract(EXCEPTION_SUMMARY_PROMPT_VERSION, EXCEPTION_SUMMARY_SYSTEM_PROMPT),
}

def prompt_for(task: ModelTask) -> PromptContract:
    try: return _PROMPTS[task]
    except (KeyError, TypeError) as exc:
        raise UnsupportedModelTaskError("model prompt is not registered") from exc
