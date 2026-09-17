"""Deterministic request budget guard."""


def enforce_character_budget(messages: list[dict[str, str]], token_budget: int) -> None:
    # Conservative approximation avoids provider tokenization in orchestration.
    approximate_tokens = sum(len(message.get("content", "")) for message in messages) // 3 + 1
    if approximate_tokens > token_budget:
        raise ValueError("model input exceeds configured token budget")
