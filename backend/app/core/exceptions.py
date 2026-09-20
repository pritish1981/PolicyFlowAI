"""Typed application failures exposed at service boundaries."""


class PolicyFlowError(Exception):
    code = "POLICYFLOW_ERROR"
    retryable = False


class ModelUnavailableError(PolicyFlowError):
    code = "MODEL_TEMPORARILY_UNAVAILABLE"
    retryable = True


class StructuredOutputError(PolicyFlowError):
    code = "MODEL_OUTPUT_INVALID"


class RerankerUnavailableError(PolicyFlowError):
    code = "RERANKER_TEMPORARILY_UNAVAILABLE"
    retryable = True


class RetrievalUnavailableError(PolicyFlowError):
    code = "POLICY_RETRIEVAL_UNAVAILABLE"
    retryable = True


class IdempotencyConflictError(PolicyFlowError):
    code = "IDEMPOTENCY_CONFLICT"


class ReviewConflictError(PolicyFlowError):
    code = "REVIEW_CONFLICT"


class ExceptionIneligibleError(PolicyFlowError):
    code = "EXCEPTION_INELIGIBLE"
