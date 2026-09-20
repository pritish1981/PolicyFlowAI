## Context

See `proposal.md` for motivation. Phase 006 already provides an allow-listed local Model Gateway telemetry hook and typed usage metadata, while Policy Q&A and expense graphs emit stage-specific structured logs. There is no shared trace context, LangSmith exporter, retrieval/citation span model, or executable evaluation pipeline. `metrics.py`, `langwatch.py`, the Ragas runner, the DeepEval runner, and the RAG evaluation workflow are placeholders. The repository has ten Policy Q&A and ten expense golden cases. LangSmith 0.8.7 is installed in one developer Python environment indirectly, but it is not a declared project dependency; Ragas and DeepEval are not installed.

The design must preserve existing API contracts, deterministic Decimal decisions, database-backed evidence/citation validation, PostgreSQL business truth, LangGraph checkpoint separation, and authorized human exception outcomes. The working tree also contains uncommitted Phase 006 implementation and documentation, so Phase 007 edits must remain scoped and must not overwrite unrelated files.

## Goals / Non-Goals

**Goals:**

- Provide an optional, fail-open LangSmith integration with consistent correlation and privacy-safe metadata.
- Make high-value graph, retrieval, Model Gateway, citation, decision, and HITL stages diagnosable as one logical trace without serializing full state.
- Turn the existing golden datasets into reproducible deterministic quality gates and comparable retrieval benchmarks.
- Provide version-compatible, operator-invoked Ragas and DeepEval paths that establish baselines without making external judges a default CI dependency.
- Generate auditable JSON and Markdown reports and publish deterministic CI artifacts.

**Non-Goals:**

- Change retrieval algorithms, prompts, model providers, vector storage, API contracts, business decisions, citation authority, or reviewer authorization.
- Run Ragas or DeepEval synchronously in application requests.
- Add CloudWatch, Prometheus, Grafana, production dashboards/alerts, durable cost accounting, or Phase 008 deployment infrastructure.
- Export full prompts, document bodies, justifications, reviewer comments, raw provider responses, credentials, or customer telemetry.

## Decisions

### 1. Use a thin project-owned tracing facade over LangSmith

`backend/app/observability/tracing.py` will expose a small span/run abstraction and preserve structured local logging. LangSmith-specific initialization and SDK interaction will live behind an optional adapter so application modules do not import LangSmith directly. Disabled tracing returns a no-op span; export failures are caught, sanitized, locally recorded, and never alter workflow results.

This is preferred over decorating every function because decorators obscure correlation inputs, can double-trace LangGraph/model calls, and make disabled behavior harder to test. Direct LangSmith calls throughout business modules were rejected because they couple business logic to one exporter.

### 2. Keep trace context explicit and immutable

A compact context object will carry existing `request_id`, `thread_id`, `scenario`, and optional `expense_id`, `exception_id`, and `review_id`. API/service boundaries create it from existing IDs; graph and gateway code pass or derive it without generating unrelated IDs. LangGraph invocation configuration may carry trace callbacks/tags when supported by the installed versions, while node helpers receive only the safe context needed for explicit stage spans.

Global mutable correlation state was rejected because async API requests, graph resumes, and worker-thread psycopg compatibility can cross execution contexts. `contextvars` may be used only as a convenience inside a request and never as the sole source of correlation truth.

### 3. Trace high-value stages, not every helper

Policy Q&A will trace validation/filtering, hybrid retrieval, fusion, reranking, gateway generation, citation validation, and final response. Expense assessment will trace intake, evidence retrieval, rule extraction, source validation, deterministic evaluation, and persistence/result mapping. Exception review will trace summary generation, interrupt, authorized action, resume, and finalization. Each stage records start/end timing, outcome, and a normalized error category.

Tracing every helper was rejected because it increases cost/noise and risks state leakage without improving the required debugging questions.

### 4. Reuse Phase 006 Model Gateway telemetry

The existing `ModelUsage` and sanitized gateway metadata remain the source for provider/model/prompt/token/retry/fallback fields. The gateway hook will publish through the shared facade and link to the active workflow trace. Provider adapters will not add a second model trace. When token counts are unavailable, fields remain null rather than estimated as provider usage.

### 5. Centralize metadata minimization before export

`redaction.py` will recursively allow-list keys and safe scalar/list values, bound string/list sizes, normalize UUID/Decimal/date/enum values, and redact known credential/header/connection/free-text keys. Raw query, prompt, policy content, expense purpose, justification, reviewer comments, exception information, provider payload, and exception text are excluded. Local structured logs will use the same safe metadata builders where practical.

Substring-only secret replacement was rejected because it cannot reliably classify nested payloads or prevent excessive policy/user text from being exported.

### 6. Normalize error categories without replacing domain errors

An observability-only mapper will classify existing exceptions into stable categories such as validation, retrieval, reranker, timeout, rate limit, model validation, guardrail, citation, workflow conflict, and database errors. It records categories but never changes exceptions, retryability, HTTP mappings, or business outcomes.

### 7. Separate runtime tracing from offline evaluation packages

Runtime code may depend on LangSmith only through the optional adapter. Ragas and DeepEval imports remain inside offline runner modules so normal API import/startup does not require evaluator initialization or credentials. Compatible dependency ranges will be selected after checking current official APIs in the resolved environment and captured in `backend/requirements.txt`; tests will exercise adapters with mocks and graceful skips.

Putting evaluator imports in application startup was rejected because dependency or credential failures could break production flows.

### 8. Treat local JSON datasets as the reproducible source of truth

The existing datasets will be extended rather than replaced. A schema/version field and validation layer will define unique IDs, queries/expenses, expected policy/section/chunk relevance, expected facts, and exact outcomes. Optional LangSmith dataset synchronization may be added only as a manual helper; it will not become required for CI reproducibility.

### 9. Implement deterministic metrics independently of LLM judges

Pure functions will compute Precision@5, Recall@10, MRR, citation correctness/coverage, and decision accuracy. Initial configurable deterministic gates are Precision@5 >= 0.80, Recall@10 >= 0.90, citation correctness >= 0.95, and decision accuracy = 1.00 unless OpenSpec review changes them before apply. Reports will include per-case numerators/denominators so failures are explainable.

Ragas/DeepEval will evaluate answer grounding/relevance/context usage only. They will not judge Decimal comparisons, receipt rules, variance, enums, or authorization.

### 10. Benchmark strategies through evaluator composition, not production mutation

The benchmark runner will invoke vector-only, hybrid RRF, and hybrid-plus-reranker compositions explicitly against the same dataset and filters. It will not rewrite application settings or persist strategy changes. Each result includes metric aggregates and measured wall-clock latency; reranker unavailability is reported as a distinct benchmark condition rather than silently presented as reranked quality.

### 11. Baseline external metrics before enforcing thresholds

Ragas and DeepEval runners will produce reports when credentials and evaluator configuration exist. Missing credentials yield an explicit skip report and successful default-CI behavior. Initial external scores are baselines; a future reviewed configuration can introduce regression tolerances. The deterministic CI gates remain enforceable immediately.

### 12. Make reports deterministic and CI-friendly

Evaluation commands will write JSON reports with schema version, timestamp, dataset hash, configuration, dependency/metric versions, per-case values, aggregates, thresholds, status, and errors. A concise Markdown summary will link the reports. CI will run deterministic dataset/metric/benchmark smoke tests and upload reports; live evaluation is manual or separately scheduled behind secrets.

Generated reports will avoid raw sensitive content. Stable checked-in baseline/report fixtures may be committed when intentional, while ephemeral live reports should be CI artifacts or ignored according to repository policy.

## Risks / Trade-offs

- **LangGraph and LangSmith integrations can double-create model spans** → keep provider calls behind the Model Gateway, configure one callback/tracing path, and assert span counts with mocked exporters.
- **Tracing latency or exporter outage could affect requests** → no-op disabled path, bounded/non-authoritative export handling, no synchronous retries in business flows, and outage tests.
- **Metadata redaction may remove useful debugging context** → prefer identifiers, ranks, counts, categories, hashes, and bounded safe fields; test the allow-list contract explicitly.
- **Ragas/DeepEval APIs and dependency trees change rapidly** → select compatible versions during apply, isolate imports/adapters, record versions in reports, and test dataset conversion independently.
- **Embedding/reranker availability can make benchmark results environment-dependent** → record models/providers/fallbacks and distinguish deterministic metric correctness from environment-specific score baselines.
- **Golden cases can encode incomplete relevance judgments** → validate schemas, cover all six synthetic policies plus abstention and decision states, and report case-level evidence for review.
- **Current dirty worktree could mix phases during publication** → preserve unrelated files and audit the eventual staged file set explicitly.

## Migration Plan

1. Add compatible dependencies and disabled-by-default configuration.
2. Add redaction, context, error mapping, no-op tracing, and mocked tests before instrumenting workflows.
3. Instrument gateway and high-value workflow stages incrementally, running Phase 003–006 regressions after each group.
4. Extend datasets and add deterministic metrics/runners, then establish retrieval/decision report baselines.
5. Add optional Ragas/DeepEval runners and explicit skip behavior.
6. Replace the placeholder CI workflow with deterministic gates and report artifacts.
7. Document local/CI/live commands and validate OpenSpec strictly.

Rollback is configuration-first: disable tracing to remove external runtime effects. Code rollback removes instrumentation and evaluation additions without database migration or business-data transformation. Golden datasets and reports remain reusable test assets.
