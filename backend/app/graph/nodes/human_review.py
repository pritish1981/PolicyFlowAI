"""Durable LangGraph human-review boundary."""
from langgraph.types import interrupt


def human_review(state: dict) -> dict:
    payload = {key: state.get(key) for key in (
        "exception_id", "expense_id", "expense", "variance_amount",
        "exception_justification", "review_summary", "summary_status", "citations")}
    response = interrupt(payload)
    return {"reviewer_decision": response["decision"],
            "reviewer_comments": response["comments"],
            "reviewer_id": response["reviewer_id"]}
