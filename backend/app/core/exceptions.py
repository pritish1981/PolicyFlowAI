"""Typed application failures exposed at service boundaries."""


class PolicyFlowError(Exception):
    code = "POLICYFLOW_ERROR"
    retryable = False


class ModelUnavailableError(PolicyFlowError):
    code = "MODEL_TEMPORARILY_UNAVAILABLE"
    retryable = True


class StructuredOutputError(PolicyFlowError):
    code = "MODEL_OUTPUT_INVALID"

class GatewayError(PolicyFlowError):
    code = "MODEL_GATEWAY_ERROR"

class UnsupportedModelTaskError(GatewayError):
    code = "MODEL_TASK_UNSUPPORTED"

class TokenBudgetExceededError(GatewayError):
    code = "MODEL_TOKEN_BUDGET_EXCEEDED"

class GuardrailViolationError(GatewayError):
    code = "MODEL_GUARDRAIL_VIOLATION"

class ProviderTimeoutError(ModelUnavailableError):
    code = "MODEL_PROVIDER_TIMEOUT"

class ProviderRateLimitError(ModelUnavailableError):
    code = "MODEL_PROVIDER_RATE_LIMITED"

class ProviderUnavailableError(ModelUnavailableError):
    code = "MODEL_PROVIDER_UNAVAILABLE"

class StructuredOutputValidationError(StructuredOutputError):
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
