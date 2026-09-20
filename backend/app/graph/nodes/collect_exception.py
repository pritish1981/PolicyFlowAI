"""Prepare deterministic exception context without deciding the outcome."""


def collect_exception(state: dict) -> dict:
    if state.get("decision", {}).get("decision") != "NEEDS_REVIEW":
        raise ValueError("exception review requires a NEEDS_REVIEW assessment")
    return {"requires_human": True, "scenario": "exception_review"}
