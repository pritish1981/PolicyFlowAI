"""Typed evidence packet checks; database validators remain authoritative."""
from app.core.exceptions import GuardrailViolationError
from app.gateway.models import EvidenceContext

def validate_evidence(items: list[EvidenceContext], max_chunks: int, max_chars: int) -> None:
    if len(items) > max_chunks or sum(len(i.content) for i in items) > max_chars:
        raise GuardrailViolationError("policy evidence exceeds governed context bounds")
    if any(not i.chunk_id or not i.approved_corpus or not i.eligible or i.status != "ACTIVE" for i in items):
        raise GuardrailViolationError("policy evidence is not eligible for model context")
