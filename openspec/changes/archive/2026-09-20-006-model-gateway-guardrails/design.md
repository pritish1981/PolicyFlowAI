## Context

See `proposal.md` and `specs/model-governance/spec.md`. Phases 003-005 already use `ModelGateway.invoke_structured` for `POLICY_QA`, `EXPENSE_POLICY_RULE`, and `EXCEPTION_REVIEW_SUMMARY`. The gateway currently provides one provider protocol, one OpenAI adapter, a global model route, approximate character-based input checking, `asyncio` timeout, bounded transient retry, Pydantic validation, and basic usage metadata. Evidence-only prompts are versioned constants, and only the OpenAI adapter imports the SDK.

Governance is nevertheless split: API routes construct concrete providers independently; callers select prompts and prompt versions; `ModelContext` is discarded; route policy is global; validation repair repeats the original request; transport and validation attempts share a counter; guardrail and observability modules are placeholders; error classification and telemetry are incomplete. Existing RAG eligibility, citation verification, deterministic expense evaluation, PostgreSQL business truth, checkpoint separation, and human reviewer authority must be reused unchanged.

The repository names its retrieval capability `policy-ingestion-and-hybrid-rag`, not `policy-rag`. The FRD is stored under `docs/architecture/`, not the supplied `docs/requirements/` path. These naming differences do not change the governing requirements.

## Goals / Non-Goals

**Goals:**

- Make the gateway the single enforcement point for provider-neutral model invocation policy.
- Give each supported task an explicit, testable route and prompt contract.
- Separate transport retry, structured-output repair, fallback, and deterministic business failure.
- Enforce bounded input/evidence/output behavior and preserve typed results.
- Provide sanitized metadata hooks sufficient for later Phase 007 instrumentation.
- Migrate all three existing call sites without changing their external business behavior.

**Non-Goals:**

- Move database-backed policy eligibility, citation truth, monetary rules, receipt rules, confidence, or human authorization into the model layer.
- Add a new business workflow, classifier, vector store, model fine-tuning, or second required live provider.
- Implement full LangSmith/LangWatch dashboards, Ragas/DeepEval pipelines, cost persistence, or Phase 007 alerting.
- Add migrations, AWS deployment, enterprise SSO, multi-agent routing, or frontend features.

## Decisions

### 1. Use one provider-neutral invocation envelope and result

Introduce immutable or strict models for gateway context, provider request/response, route policy, usage, and gateway result. Context carries `request_id`, optional `thread_id`, scenario, and sanitized metadata. The gateway result carries the validated typed output and usage/route metadata; raw provider responses never escape the adapter.

Keep `invoke_structured(task, ..., output_schema, context)` as the public compatibility shape while migrating message assembly toward the prompt registry. A protocol-only gateway was rejected because the runtime needs one concrete enforcement pipeline; callers can still depend on a narrow protocol in tests if useful.

### 2. Define route policy as data keyed by task

Replace the single `route_model()` result with a `ModelRoutePolicy` per `ModelTask`. It owns primary model, optional fallback model, input budget, output cap, timeout, transport retries, repair allowance, and fallback-eligible error categories. `POLICY_QA` and `EXPENSE_POLICY_RULE` use the primary reasoning/structured-output route; `EXCEPTION_REVIEW_SUMMARY` may use a lower-cost configured route while keeping identical safety controls.

Task configuration uses settings defaults plus optional task-specific environment overrides. No provider model name remains in graph nodes or services. `CLASSIFY_INTENT` is not added because current API/workflow routing is deterministic and no implementation call site requires it.

### 3. Centralize prompt templates and versions without trusting evidence text

Create a prompt registry that resolves a task to its system prompt, version, builder, and expected authority constraints. Existing prompt content is preserved, strengthened where necessary, and split into task modules only if that improves ownership. System instructions clearly separate system rules, user input, and policy evidence and state that evidence is untrusted data whose embedded instructions must be ignored.

The gateway resolves prompt version; callers cannot supply an arbitrary default. An unregistered prompt is a pre-provider error. Keeping prompt constants scattered in callers was rejected because it prevents reliable version/route telemetry.

### 4. Keep authoritative evidence validation in RAG and add a gateway evidence envelope

Existing retrieval filters and `validate_citations` remain authoritative because they query stored document/chunk state and effective dates. The gateway receives typed evidence descriptors produced by the server, checks required IDs/metadata, bounded count/size, ACTIVE/effective flags, and approved-corpus provenance before prompt construction, then treats content as untrusted data.

This is defense in depth, not a second source of policy truth. Moving SQL eligibility into the gateway was rejected because it would couple provider orchestration to persistence and duplicate Phase 002/003 logic. Accepting arbitrary caller text as trusted evidence was also rejected.

### 5. Layer deterministic guardrails around the provider call

The gateway pipeline is:

```text
task/context/input
  -> route and prompt registry
  -> input/scenario/injection checks
  -> evidence-context checks
  -> request budget
  -> primary provider with timeout/transient retry
  -> schema validation
  -> at most one explicit repair attempt
  -> task output guardrails
  -> optional eligible fallback through the same pipeline
  -> typed result plus sanitized metadata
```

Input heuristics detect a bounded set of injection patterns and produce a deterministic violation/warning outcome; they never decide policy. Output checks enforce task authority: policy answers cite only supplied IDs, rule extraction has no final decision, and exception summaries have neither decision fields nor authoritative approval/rejection language. Existing downstream citation/rule validation remains mandatory.

### 6. Separate request budgets from transient thread accounting

Estimate tokens deterministically without requiring provider tokenizers in orchestration, using a documented conservative approximation. Apply per-task input and output limits. Do not silently truncate required evidence. Optional context reduction may remove only explicitly optional material while retaining full evidence units and recording the action; otherwise fail with `TokenBudgetExceededError`.

Per-thread accounting is optional and transient. If implemented with Redis, use a namespaced TTL key and fail safely according to configuration; business records, decisions, and review state never depend on the counter. The current `THREAD_TOKEN_BUDGET` value must no longer masquerade as the per-request limit.

### 7. Separate transport retries validation repair and fallback

Transport retry handles only timeout, connection, 429, and provider 5xx categories using configurable bounded exponential backoff. Non-transient input, guardrail, evidence, citation, and business failures are never retried.

After a schema failure, issue at most one explicit repair request containing the schema failure category and the original governed context, without raw secrets. Record `validation_retry_count` separately. A second invalid result raises `StructuredOutputValidationError`.

Fallback is optional and model/provider neutral. It is attempted only after a configured technical category is exhausted, never for insufficient evidence or to seek a different business result, and it passes through all budgets, guardrails, schema validation, and output checks. No second provider is required for local/CI completion.

### 8. Introduce a precise provider-neutral error taxonomy

Add gateway errors for unsupported task, token budget, guardrail violation, provider timeout, provider rate limit, provider unavailable, and structured-output validation while retaining compatibility with current `ModelUnavailableError` and `StructuredOutputError` at API boundaries. Provider adapters translate SDK failures; graph/services never import provider exception types.

Policy Q&A and expense assessment retain controlled 503/insufficient-information behavior. Exception summary continues fail-open-to-human, but catches classified gateway failures explicitly and emits sanitized metadata rather than swallowing all diagnostic categories. Deterministic rule rejection and reviewer conflicts do not enter gateway fallback/retry logic.

### 9. Centralize gateway construction outside API routes

Create a cached dependency/factory that builds configured primary and optional fallback adapters and the gateway. Policy, expense, and review routes depend on the same construction path. A local unavailable adapter can remain provider-neutral for no-key operation and tests.

This removes concrete `OpenAIProvider` imports and repeated stubs from routes. It does not create a global mutable client; adapter/client lifetime can be cached according to SDK safety while dependency overrides remain available for tests.

### 10. Expose telemetry metadata but defer Phase 007 instrumentation

Successful results include task, provider, model, prompt version, input/output/total tokens when available, total latency, transport retry count, validation retry count, fallback flag, guardrail outcome, request ID, and thread ID. Failures emit the same correlation fields plus error category and retryability through a small provider-neutral hook or structured logger.

Raw prompts, policy bodies, employee justification, authorization headers, keys, and database credentials are excluded. `observability/tracing.py` and `metrics.py` may define no-op or logging hooks, but external exporters, dashboards, quality metrics, and evaluation pipelines remain Phase 007.

### 11. Preserve business semantics at each migrated call site

- Policy Q&A still retrieves/reranks first, invokes `POLICY_QA`, validates citations against authoritative storage, and safely abstains.
- Expense assessment still invokes `EXPENSE_POLICY_RULE`, validates rule sources/amounts, and applies Decimal/document rules in Python.
- Exception review still invokes `EXCEPTION_REVIEW_SUMMARY`; failure marks summary unavailable and only a reviewer finalizes the exception.

No graph node or service invokes a provider SDK. No Phase 006 change rewrites deterministic decision logic, checkpoint behavior, business transactions, or API response contracts.

### 12. Test through injected provider adapters

Create a reusable scripted fake adapter that can produce valid output, invalid output, recovery on repair, timeout, rate limit, server error, non-transient error, and usage metadata. Tests inject adapters/factories instead of monkey-patching graph internals. The existing OpenAI adapter contract test may patch the SDK at the adapter boundary only.

Targeted tests cover routing, budgets, retries, repair, fallback, guardrails, errors, prompt versions, telemetry, and provider isolation. Existing Phase 003-005 suites prove no business regression; no live credential is required.

## Risks / Trade-offs

- **Injection heuristics produce false positives** -> Keep patterns deterministic, narrow, observable, task-configured, and non-authoritative; test allowed policy language separately.
- **Approximate token counting differs from provider billing** -> Use conservative budgets and provider-reported usage for telemetry; avoid claiming exact pre-call counts.
- **Gateway evidence checks drift from database eligibility** -> Keep database validators authoritative and pass typed eligibility metadata; test both layers without copying SQL into the gateway.
- **Fallback doubles latency or cost** -> Restrict it to configured technical categories, record use, and omit it entirely when no route is configured.
- **Repair prompts leak invalid raw output** -> Include only bounded sanitized output/error context and never secrets or full provider payloads.
- **Route configuration becomes fragmented** -> Resolve every task through one policy table with settings-derived values and validate it at startup/test time.
- **Thread accounting makes Redis a dependency** -> Keep it optional/transient and never let unavailable counters change persisted business truth.
- **Catch-all summary behavior hides defects** -> Preserve fail-open-to-human but classify/log sanitized gateway failures and keep unexpected application failures distinguishable.

## Migration Plan

1. Strictly validate all planning artifacts before code changes.
2. Add provider-neutral contracts, errors, route policy, prompt registry, guardrail pipeline, and tests while preserving the current public gateway entry point.
3. Harden the OpenAI adapter and add optional fallback construction; verify SDK imports remain adapter-only.
4. Migrate Policy Q&A, expense-rule, and exception-summary callers one at a time, running their existing regression suites after each migration.
5. Run gateway-focused tests, all Phase 003-005 tests, the full backend suite, frontend tests/build, direct-SDK search, secret/whitespace checks, and strict OpenSpec validation.
6. Rollback restores the previous gateway implementation and route construction; no database downgrade is required. Existing business, RAG, and checkpoint data remain compatible.
