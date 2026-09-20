## 1. Gateway Contracts and Configuration

- [x] 1.1 Add strict provider-neutral gateway context, message/evidence, request, response, usage, route-policy, and typed-result models; verify model unit tests reject unsupported fields and no provider SDK types appear in public contracts.
- [x] 1.2 Add provider-neutral gateway error categories for unsupported task, budget, guardrail, timeout, rate limit, unavailable provider, and invalid structured output; verify unit tests assert code, retryability, and sanitized public messages.
- [x] 1.3 Extend settings with primary/fallback and task-specific model, input/output budget, timeout, retry-delay, validation-repair, and thread-budget controls; verify configuration tests cover defaults and environment overrides without exposing secrets.

## 2. Task Routing and Prompt Governance

- [x] 2.1 Replace the global model lookup with one immutable route-policy registry for `POLICY_QA`, `EXPENSE_POLICY_RULE`, and `EXCEPTION_REVIEW_SUMMARY`; verify routing tests cover every task, task-specific limits, fallback eligibility, and unsupported-task rejection.
- [x] 2.2 Implement a central prompt registry with explicit versions and evidence/authority constraints for all three tasks; verify prompt tests resolve known tasks and reject missing templates or versions before provider invocation.
- [x] 2.3 Strengthen prompt construction so system rules, user input, and untrusted policy evidence are separated and embedded evidence instructions are ignored; verify prompt snapshot/assertion tests cover evidence-only, citation, deterministic-decision, and human-authority language.

## 3. Provider Abstraction and Construction

- [x] 3.1 Refactor the provider protocol to accept a provider-neutral request and return a provider-neutral response with usage metadata; verify a scripted fake adapter can simulate success and failure without importing OpenAI types.
- [x] 3.2 Harden the OpenAI adapter to translate SDK timeout, 429, connection, server, and non-transient failures into gateway categories while returning no raw SDK object; verify adapter-boundary tests with a patched SDK client.
- [x] 3.3 Add one cached gateway factory/dependency for configured primary, optional fallback, and no-key unavailable adapters; verify route dependency overrides still work and API modules no longer construct `OpenAIProvider` or duplicate unavailable-provider classes.
- [x] 3.4 Search backend source for `openai`, `OpenAI`, and `AsyncOpenAI`; verify direct SDK import/client construction exists only in the OpenAI adapter and document any intentional test-boundary usage.

## 4. Token and Thread Budget Controls

- [x] 4.1 Replace the current thread-budget-as-request-limit behavior with documented conservative input estimation and per-task request limits; verify within-limit input passes and over-limit input fails before provider invocation.
- [x] 4.2 Pass each route's output-token cap to primary, repair, and fallback provider calls; verify fake-provider assertions for all supported tasks.
- [x] 4.3 Implement transient per-thread token accounting with a namespaced Redis TTL counter or equivalent existing transient abstraction, including configured safe degradation; verify unavailable Redis never changes persisted expense, assessment, exception, or review state.
- [x] 4.4 Prevent silent truncation of authoritative evidence and allow only whole optional-context reduction when explicitly safe; verify an irreducible over-budget evidence packet returns a controlled budget error.

## 5. Guardrail Pipeline

- [x] 5.1 Implement deterministic input validation for non-empty normalized messages, supported task/scenario combinations, request-size bounds, and malformed content; verify violations occur before provider invocation.
- [x] 5.2 Implement bounded prompt-injection heuristics for instruction override, system-prompt disclosure, policy override, and evidence-disregard patterns; verify detected input produces sanitized guardrail metadata without becoming policy logic.
- [x] 5.3 Add typed retrieval-context checks for chunk identity, approved synthetic provenance, ACTIVE/effective eligibility flags, metadata presence, maximum evidence count, and maximum context size; verify arbitrary or ineligible evidence is never sent to a provider.
- [x] 5.4 Reuse existing database-backed citation and policy-rule validators as authoritative downstream controls; verify gateway checks do not replace or weaken current ACTIVE/effective/source validation.
- [x] 5.5 Implement task output guardrails for supplied citation IDs, absence of final expense decisions in rule extraction, and absence of approval/rejection authority in exception summaries; verify invalid output is rejected or safely marked unavailable.

## 6. Timeout Retry Repair and Fallback

- [x] 6.1 Implement explicit per-route timeout and provider-neutral timeout mapping; verify a fake timeout never blocks indefinitely and produces the configured safe error.
- [x] 6.2 Implement configurable bounded exponential backoff for timeout, connection, 429, and provider 5xx failures only; verify maximum attempts and delay scheduling while non-transient failures are not retried.
- [x] 6.3 Separate transport retry count from structured-output validation retry count; verify telemetry distinguishes both counters.
- [x] 6.4 Implement one explicit bounded schema-repair attempt with the registered schema/prompt policy; verify first-invalid/second-valid succeeds once and two invalid results raise a safe structured-output error.
- [x] 6.5 Implement optional primary-to-fallback routing for configured technical categories through identical budgets, guardrails, schema validation, and output checks; verify fallback is recorded and never runs for insufficient evidence, citation rejection, guardrail violation, or business-rule outcomes.

## 7. Gateway Orchestration and Telemetry Hooks

- [x] 7.1 Rebuild `ModelGateway.invoke_structured` as the ordered route, prompt, guardrail, budget, provider, retry, repair, output-guardrail, fallback, and typed-result pipeline; verify focused gateway integration tests cover the complete order.
- [x] 7.2 Preserve request/thread/scenario context instead of discarding it and return task, provider, model, prompt version, input/output/total tokens, latency, retry counts, fallback, guardrail, and correlation metadata; verify result-model tests cover available and unavailable token usage.
- [x] 7.3 Add sanitized success/failure telemetry hooks in the existing observability modules without external exporters; verify captured events contain required metadata and exclude API keys, credentials, full policy content, raw provider payloads, and unnecessary justification/query text.

## 8. Existing Call-Site Migration

- [x] 8.1 Migrate Policy Q&A to the governed route/prompt/evidence context while preserving authoritative citation validation and safe abstention; verify existing Policy Q&A unit, adapter, and live retrieval tests pass.
- [x] 8.2 Migrate expense policy-rule extraction while preserving exact source/amount validation and deterministic Decimal evaluation; verify INR 6500 versus 7000 remains `COMPLIANT`, INR 9500 versus 7000 remains `NEEDS_REVIEW`, and invalid citations remain `INSUFFICIENT_INFORMATION`.
- [x] 8.3 Migrate exception-summary generation while preserving citation-subset checks and fail-open-to-human behavior; verify provider, guardrail, or schema failure marks the summary unavailable and never changes reviewer authority.
- [x] 8.4 Replace route-level provider construction in policy, expense, and review APIs with the shared dependency while preserving dependency injection; verify API tests cover no-key controlled behavior and all current response contracts.

## 9. Focused and Regression Verification

- [x] 9.1 Add reusable scripted fake-provider fixtures for success, usage metadata, timeout, 429, 5xx, non-transient failure, invalid schema, successful repair, repeated invalid output, and fallback; verify all scenarios run without live credentials.
- [x] 9.2 Add focused model-governance unit and integration suites covering routing, prompts, budgets, thread accounting, retries, repair, fallback, guardrails, errors, provider isolation, and telemetry; verify all new tests pass.
- [x] 9.3 Run Phase 003 Policy Q&A regression tests and verify grounded answers, citation rejection, abstention, and controlled provider failure remain unchanged.
- [x] 9.4 Run Phase 004 expense regression tests and verify intake, clarification, idempotency, retrieval, rule extraction, deterministic decisions, and persistence remain unchanged.
- [x] 9.5 Run Phase 005 exception/HITL regression tests and verify interrupt/resume, summary failure, concurrency, more-information continuation, audit, and human-only finalization remain unchanged.
- [x] 9.6 Run the complete backend suite against required PostgreSQL/Redis fixtures and verify every collected test passes with no live OpenAI dependency.
- [x] 9.7 Run frontend tests and production build and verify Phase 006 introduces no UI or typed-client regression.

## 10. Documentation and OpenSpec Completion

- [x] 10.1 Update README and consolidated local-validation guidance with task routes, configuration, safe failures, credential-free tests, direct-SDK audit, and expected results; verify commands are checkout-aware and copyable on Windows.
- [x] 10.2 Run secret-signature and staged/working-tree whitespace checks and verify no `.env`, credential, raw provider payload, or unrelated user file enters the Phase 006 scope.
- [x] 10.3 Run strict validation for `006-model-gateway-guardrails`, canonical specs, and all OpenSpec content; verify zero failures and keep task checkboxes aligned only with completed evidence.
- [x] 10.4 Produce the Phase 006 implementation report with changed files, call sites, direct-SDK audit, retry/repair/token/guardrail behavior, telemetry fields, targeted/full/frontend/OpenSpec results, known limitations, and explicit Phase 007 deferrals; stop without beginning Phase 007.
