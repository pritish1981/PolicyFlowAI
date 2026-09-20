"""Immutable correlation metadata shared by runtime tracing stages."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TraceContext:
    request_id: str
    thread_id: str
    scenario: str
    expense_id: str | None = None
    exception_id: str | None = None
    review_id: str | None = None

    def metadata(self) -> dict[str, str]:
        return {key: value for key, value in {
            "request_id": self.request_id, "thread_id": self.thread_id,
            "scenario": self.scenario, "expense_id": self.expense_id,
            "exception_id": self.exception_id, "review_id": self.review_id,
        }.items() if value is not None}

    @classmethod
    def from_state(cls, state: dict) -> "TraceContext":
        request_id = str(state.get("request_id") or "unknown")
        return cls(request_id=request_id,
                   thread_id=str(state.get("thread_id") or request_id),
                   scenario=str(state.get("scenario") or "unknown"),
                   expense_id=_text(state.get("expense_id")),
                   exception_id=_text(state.get("exception_id")),
                   review_id=_text(state.get("review_id")))


def _text(value: object) -> str | None:
    return None if value is None else str(value)
