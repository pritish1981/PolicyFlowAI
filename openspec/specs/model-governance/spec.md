## Purpose

Provides a single governed, provider-neutral boundary for every model invocation, with explicit routing, budgets, guardrails, validation, safe failure, and traceable metadata while deterministic controls and human decisions remain authoritative.

## Requirements

### Requirement: Single governed model boundary
The system SHALL route every LLM or generative-model invocation through one provider-neutral Model Gateway and SHALL isolate provider SDK objects, exceptions, message types, and response objects inside provider adapters.

#### Scenario: Supported application model call
- **WHEN** Policy Q&A, expense policy-rule extraction, or exception-summary generation requires a model
- **THEN** the caller invokes the Model Gateway with a supported task, typed context, messages or prompt inputs, and an expected response schema

#### Scenario: Direct provider coupling audit
- **WHEN** the backend source is inspected for direct provider SDK imports or client construction
- **THEN** such usage exists only inside the corresponding provider adapter

### Requirement: Explicit task policy and routing
The system SHALL define one testable route policy for each supported model task containing its prompt version, preferred model route, maximum input budget, maximum output tokens, timeout, transient retry limit, response schema expectation, and fallback eligibility. At minimum, `POLICY_QA`, `EXPENSE_POLICY_RULE`, and `EXCEPTION_REVIEW_SUMMARY` SHALL be supported.

#### Scenario: Supported task route
- **WHEN** a supported model task is invoked
- **THEN** the gateway applies that task's configured route policy without requiring a graph node or service to select a provider-specific model

#### Scenario: Unsupported task
- **WHEN** a caller requests an unknown or unconfigured task
- **THEN** the gateway rejects it before provider invocation with a non-retryable provider-neutral error

### Requirement: Versioned prompt governance
The system SHALL resolve the system prompt and explicit prompt version for every supported task from a central prompt registry and SHALL include that version in successful and failed invocation metadata.

#### Scenario: Known prompt
- **WHEN** the gateway prepares a supported task
- **THEN** it uses the registered evidence and authority constraints and records the registered prompt version

#### Scenario: Unknown prompt registration
- **WHEN** a task has no registered prompt or prompt version
- **THEN** the gateway fails safely before contacting a provider

### Requirement: Deterministic input and retrieval-context guardrails
The system SHALL reject empty or malformed model input, enforce supported task and scenario combinations, apply deterministic prompt-injection heuristics, and accept policy evidence only from server-produced context that contains bounded chunk identifiers and required eligibility metadata. Guardrail heuristics SHALL NOT make policy or expense decisions.

#### Scenario: Prompt-injection pattern
- **WHEN** input asks the model to ignore governing instructions, reveal a system prompt, override policy, or disregard supplied evidence
- **THEN** the gateway records a sanitized guardrail outcome and rejects or safely handles the invocation according to the task policy without treating the text as authoritative instructions

#### Scenario: Ineligible or arbitrary evidence
- **WHEN** a policy-related request contains evidence that lacks a chunk identifier, approved-corpus provenance, ACTIVE status, or valid effective interval
- **THEN** the gateway does not send that evidence to a provider and returns a controlled guardrail or insufficient-evidence outcome

#### Scenario: Eligible bounded evidence
- **WHEN** server-produced evidence satisfies identity, status, effective-date, metadata, count, and size constraints
- **THEN** the gateway may include it as untrusted data under evidence-only system instructions

### Requirement: Request and output token controls
The system SHALL estimate or measure model input against the selected task's per-request budget, pass the task-specific output limit to the provider, and fail safely when a request cannot fit without removing authoritative meaning. Any thread-level accounting SHALL be transient and SHALL NOT determine authoritative business state.

#### Scenario: Request within budget
- **WHEN** normalized instructions and context fit the task input limit
- **THEN** the gateway invokes the provider with the configured output-token cap

#### Scenario: Request exceeds budget
- **WHEN** input exceeds the task limit and cannot be safely reduced without changing authoritative evidence
- **THEN** the gateway returns a non-fabricated controlled budget failure without provider invocation

#### Scenario: Thread counter unavailable
- **WHEN** optional transient thread accounting is unavailable
- **THEN** the gateway degrades according to configured safe behavior and no persisted expense, assessment, exception, or review outcome is changed by the missing counter

### Requirement: Explicit timeout and bounded transient retry
The system SHALL apply an explicit provider timeout and SHALL retry only classified transient timeout, connection, rate-limit, or provider-server failures using bounded backoff. It SHALL NOT retry invalid input, unsupported tasks, guardrail violations, citation mismatch, insufficient evidence, or deterministic business-rule outcomes.

#### Scenario: Transient provider failure
- **WHEN** a provider times out, returns a rate-limit response, returns a provider-server error, or has a temporary connection failure
- **THEN** the gateway retries no more than the configured task limit and records the retry count

#### Scenario: Non-retryable failure
- **WHEN** an invocation fails input validation, task support, guardrails, evidence validation, or another non-transient check
- **THEN** the gateway returns the classified error without transport retry

#### Scenario: Retries exhausted
- **WHEN** all permitted transient attempts fail and no eligible fallback succeeds
- **THEN** the caller receives a provider-neutral temporary-unavailability error without provider internals

### Requirement: Structured output and one repair attempt
The system SHALL validate every business-relevant model output against its registered Pydantic-compatible schema and task-specific output guardrails before returning a typed result. Invalid output MAY receive at most one bounded repair attempt distinct from transport retries; a second invalid result SHALL fail safely.

#### Scenario: Valid structured output
- **WHEN** provider output conforms to the registered schema and output guardrails
- **THEN** the gateway returns only the validated typed result and governed metadata

#### Scenario: Repair succeeds
- **WHEN** the first provider result fails structured validation and the task permits repair
- **THEN** the gateway performs one bounded repair attempt, validates it, and records one validation retry

#### Scenario: Repair fails
- **WHEN** the repair result remains invalid
- **THEN** the gateway returns a structured-output validation error and does not expose raw unvalidated content

### Requirement: Task-specific generation and output authority guardrails
The system SHALL enforce evidence-only generation and task authority boundaries in both prompt contracts and deterministic output checks. Policy Q&A SHALL not decide expense compliance, policy-rule extraction SHALL not emit a final compliance decision, and exception-summary generation SHALL not approve, reject, or recommend a reviewer outcome.

#### Scenario: Policy answer invents a source
- **WHEN** a Policy Q&A result references a chunk outside supplied evidence
- **THEN** the result cannot produce a grounded policy answer

#### Scenario: Expense rule contains a final decision
- **WHEN** expense-rule output attempts to set COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, approval, or another final decision
- **THEN** the gateway or downstream deterministic validator rejects the output and application code retains decision authority

#### Scenario: Exception summary contains decision authority
- **WHEN** summary output contains an approval/rejection field or an authoritative approval or rejection instruction
- **THEN** the output is rejected or marked unavailable and the pending human-review workflow remains authoritative

### Requirement: Guarded fallback readiness
The system SHALL support an optional fallback route behind the same request contract, response schema, token controls, guardrails, and telemetry. Fallback SHALL be eligible only for configured technical/provider failures and SHALL NOT override insufficient evidence, citation rejection, guardrail failure, or deterministic business logic.

#### Scenario: Eligible technical fallback
- **WHEN** a primary route exhausts a configured fallback-eligible technical failure and a fallback route exists
- **THEN** the gateway invokes the fallback under the same validation and guardrail requirements and records that fallback was used

#### Scenario: Business rejection is not fallback eligible
- **WHEN** evidence is insufficient, citations fail, or deterministic rules reject a conclusion
- **THEN** the gateway does not invoke fallback to obtain a different business outcome

### Requirement: Provider-neutral error taxonomy and safe behavior
The system SHALL classify unsupported task, token budget, guardrail, provider timeout, rate limit, provider unavailability, and structured-output failures without exposing provider exception details. Callers SHALL map these errors to controlled API failure, safe abstention, or continued human review according to the existing workflow contract.

#### Scenario: Policy generation unavailable
- **WHEN** Policy Q&A or expense rule extraction exhausts safe gateway handling
- **THEN** the API returns the existing controlled temporary-unavailability or insufficient-information behavior without fabricating policy facts or decisions

#### Scenario: Exception summary unavailable
- **WHEN** exception-summary generation exhausts safe gateway handling
- **THEN** the summary is marked unavailable while deterministic facts and the authorized human review remain usable

### Requirement: Sanitized gateway telemetry metadata
The system SHALL expose or emit sanitized metadata for task, provider, model, prompt version, request and thread identifiers, input/output/total tokens when available, latency, transient retry count, validation retry count, fallback use, guardrail outcome, and error category. It SHALL NOT log API keys, authorization headers, database credentials, full provider payloads, full policy documents, or unnecessary raw employee text.

#### Scenario: Successful invocation metadata
- **WHEN** a model invocation succeeds
- **THEN** its result or telemetry hook contains the governed route, correlation, token, latency, retry, validation, fallback, and prompt metadata available for that invocation

#### Scenario: Failed invocation metadata
- **WHEN** a gateway invocation fails
- **THEN** sanitized metadata identifies the task, correlation identifiers, failure category, retryability, and safe path without secrets or raw provider exception content

### Requirement: Existing authority and compatibility boundaries
The system SHALL preserve existing Policy Q&A, expense assessment, and exception-review API contracts and SHALL keep policy eligibility, citation validation, monetary and receipt rules, persisted business state, and authorized reviewer decisions outside model authority.

#### Scenario: Expense thresholds after gateway hardening
- **WHEN** verified evidence supplies a standard limit and an expense is evaluated
- **THEN** deterministic application code continues to compare Decimal amounts and choose the compliance state

#### Scenario: Human exception finalization
- **WHEN** an exception awaits review
- **THEN** no gateway result finalizes it and only an authorized reviewer action changes its authoritative review outcome
