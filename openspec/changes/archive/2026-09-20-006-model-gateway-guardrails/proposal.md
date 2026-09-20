## Why

PolicyFlow AI already routes its three business-relevant model tasks through a provider-neutral gateway, but policy enforcement remains split across callers and incomplete placeholders. Phase 006 makes the Model Gateway the single governed boundary for prompts, routing, budgets, retries, structured validation, guardrails, safe failure, and telemetry without changing deterministic policy decisions or human exception authority.

## What Changes

- Normalize provider-neutral gateway request, response, context, usage, route-policy, and error contracts while keeping OpenAI SDK behavior isolated inside its adapter.
- Define one testable route policy for `POLICY_QA`, `EXPENSE_POLICY_RULE`, and `EXCEPTION_REVIEW_SUMMARY`, including prompt version, model tier, input/output limits, timeout, retry policy, response contract, and fallback eligibility.
- Centralize prompt lookup and version governance, and construct gateway/provider dependencies once rather than in individual API routes.
- Enforce deterministic input, prompt-injection, retrieval-context, generation, output, and workflow guardrails around every model invocation.
- Separate bounded transient retries from one bounded structured-output repair attempt; map failures to provider-neutral safe errors and permit optional fallback only for documented technical failures.
- Add per-request and task-specific token controls, with optional transient thread accounting that cannot become business truth or silently truncate authoritative evidence.
- Expose sanitized task, model, prompt, token, latency, retry, validation-retry, fallback, guardrail, correlation, and error metadata through provider-neutral telemetry hooks.
- Migrate the three existing call sites without changing Policy Q&A contracts, deterministic expense rules, citation authority, exception workflows, or reviewer decisions.
- Add credential-free unit and integration tests and regression coverage for Phases 003-005.
- Keep full external observability/evaluation, new business workflows, model fine-tuning, AWS deployment, enterprise identity, multi-agent routing, and autonomous exception approval out of scope.

## Capabilities

### New Capabilities

- `model-governance`: Central provider-neutral model invocation, task routing, prompt/version control, bounded token/timeout/retry/repair behavior, layered guardrails, safe failure/fallback, and sanitized telemetry metadata.

### Modified Capabilities

None. Existing `policy-qa`, `expense-compliance`, and `exception-review` behavior and authority boundaries remain unchanged; their existing Model Gateway calls are hardened behind the new capability.

## Impact

- **Gateway and providers:** contracts, routing, prompt registry, token controls, retry/repair behavior, OpenAI adapter, optional fallback-ready construction, and gateway error taxonomy.
- **Guardrails:** deterministic input, evidence-context, output, and workflow enforcement that reuses existing citation and policy-rule validators.
- **Configuration:** primary/fallback models, task budgets, retry delay, timeout, and output limits with no hardcoded secrets.
- **Call sites:** Policy Q&A, expense policy-rule extraction, and exception review summary use one governed gateway construction path; only the OpenAI adapter imports the provider SDK.
- **Telemetry:** provider-neutral metadata hooks only; Phase 007 dashboards and evaluation frameworks remain deferred.
- **Persistence and UI:** no database migration and no intended frontend behavior change.
- **Compatibility:** existing APIs, deterministic decisions, safe abstention, checkpoint/business-state separation, and human reviewer authority remain intact.
