"""Retry classification shared by gateway providers."""


def is_transient_model_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return bool(getattr(exc, "retryable", False)) or isinstance(
        exc, (TimeoutError, ConnectionError)
    ) or status == 429 or (
        isinstance(status, int) and status >= 500
    )

def retry_delay(attempt: int, base_delay_ms: int) -> float:
    return min((base_delay_ms / 1000) * (2 ** attempt), 2.0)
