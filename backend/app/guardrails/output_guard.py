"""Task authority and citation-subset output checks."""
import re
from app.core.exceptions import GuardrailViolationError
from app.gateway.routing import ModelTask

def validate_output(task: ModelTask, output, allowed_chunk_ids: set[str]) -> None:
    cited = {str(v) for v in getattr(output, "citation_chunk_ids", [])}
    if not cited.issubset(allowed_chunk_ids):
        raise GuardrailViolationError("model output cites evidence outside the governed context")
    data = output.model_dump(mode="json")
    if task == ModelTask.EXPENSE_POLICY_RULE and any(k in data for k in ("decision", "approval")):
        raise GuardrailViolationError("policy-rule output attempted a business decision")
    if task == ModelTask.EXCEPTION_REVIEW_SUMMARY:
        text = " ".join([str(data.get("summary", "")), *data.get("key_facts", []), *data.get("risk_or_attention_points", [])])
        if re.search(r"\b(?:approv(?:e|ed|al)|reject(?:ed|ion)?)\b", text, re.I):
            raise GuardrailViolationError("exception summary attempted reviewer authority")
