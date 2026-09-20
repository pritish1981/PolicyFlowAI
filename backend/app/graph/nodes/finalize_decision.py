"""Mirror the authoritative human action into workflow output."""


def finalize_decision(state: dict) -> dict:
    mapping = {"APPROVE": "APPROVED", "REJECT": "REJECTED",
               "REQUEST_MORE_INFORMATION": "MORE_INFORMATION_REQUIRED"}
    return {"final_status": mapping[state["reviewer_decision"]], "requires_human": False}
