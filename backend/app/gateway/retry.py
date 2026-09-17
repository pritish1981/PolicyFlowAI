"""Retry classification shared by gateway providers."""


def is_transient_model_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return isinstance(exc, (TimeoutError, ConnectionError)) or status == 429 or (
        isinstance(status, int) and status >= 500
    )
