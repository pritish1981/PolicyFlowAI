"""Deterministic request and transient thread budget controls."""
from app.core.exceptions import TokenBudgetExceededError


def estimate_tokens(messages: list[dict[str, str]]) -> int:
    return sum(len(message.get("content", "")) for message in messages) // 3 + 1

def enforce_character_budget(messages: list[dict[str, str]], token_budget: int) -> int:
    # Conservative approximation avoids provider tokenization in orchestration.
    approximate_tokens = estimate_tokens(messages)
    if approximate_tokens > token_budget:
        raise TokenBudgetExceededError("model input exceeds configured token budget")
    return approximate_tokens

def consume_thread_budget(client, thread_id: str | None, tokens: int, limit: int, ttl: int) -> None:
    if not client or not thread_id: return
    try:
        key=f"thread:budget:{thread_id}"; total=client.incrby(key, tokens); client.expire(key, ttl)
        if total > limit: raise TokenBudgetExceededError("thread token budget exceeded")
    except TokenBudgetExceededError: raise
    except Exception: return  # transient counter is never business truth
