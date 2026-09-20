## 1. Dependency and Configuration Foundation

- [x] 1.1 Resolve compatible current LangSmith, Ragas, and DeepEval versions against Python 3.12 and the repository's LangGraph/OpenAI dependencies; add bounded dependency ranges and verify a clean `uv run --no-project --with-requirements backend/requirements.txt` import smoke succeeds.
- [x] 1.2 Add disabled-by-default LangSmith, evaluation-enable, dataset-path, deterministic-threshold, and optional endpoint/project settings; verify configuration tests cover defaults and environment overrides without exposing keys.
- [x] 1.3 Update the local environment template with placeholder-only Phase 007 settings while preserving the repository's `.env.example` publication rule; verify secret scanning finds no credential value and no `.env` file is staged.
- [x] 1.4 Define normalized observability error categories and typed trace/evaluation result contracts; verify unit tests cover supported mappings, unknown errors, strict fields, and serialization.

## 2. Privacy-Safe Observability Foundation

- [x] 2.1 Implement an immutable correlation context for request, thread, scenario, expense, exception, and review identifiers; verify unit tests preserve supplied IDs and never generate unrelated downstream correlation IDs.
- [x] 2.2 Implement recursive telemetry allow-listing, normalization, size bounds, and redaction for nested mappings and lists; verify tests remove API keys, headers, connection strings, prompts, policy bodies, justifications, comments, PII-like text, and raw provider payloads while retaining approved IDs/counts/scores/categories.
- [x] 2.3 Implement an optional LangSmith adapter and no-op tracer behind the project-owned tracing facade; verify disabled, missing-key, enabled-mocked, exporter-error, and concurrent-request tests require no network and never change caller results.
- [x] 2.4 Implement reusable stage-span timing and sanitized success/failure emission with normalized categories; verify mocked clock/exporter tests cover duration, hierarchy, correlation, and exception passthrough.
- [x] 2.5 Extend structured metric helpers for retrieval, citation, decision, gateway, and HITL metadata; verify every builder returns only allowed bounded fields.

## 3. Runtime Workflow Instrumentation

- [x] 3.1 Wire request/thread trace context through Policy Q&A service and graph invocation using existing identifiers; verify graph tests show one correlated trace across request validation, filtering, retrieval, fusion, reranking, gateway, citation validation, and final response.
- [x] 3.2 Instrument hybrid retrieval with filters, lexical/vector counts, chunk IDs, ranks, and latency; verify credential-free tests capture metadata without query text or document content.
- [x] 3.3 Instrument RRF and reranking with fused/reranked counts, chunk IDs, RRF/reranker scores, fallback state, and latency; verify success and configured-fallback tests preserve current ranking outputs.
- [x] 3.4 Route existing Phase 006 Model Gateway success/failure telemetry through the shared trace facade without adding provider-level duplicate spans; verify tests assert one governed model span with task/model/prompt/token/retry/fallback metadata.
- [x] 3.5 Add citation-validation telemetry for generated, valid, and invalid counts, chunk IDs, and available rejection categories while leaving the database validator authoritative; verify existing mismatch, inactive/effective, version, and metadata validation behavior remains unchanged.
- [x] 3.6 Wire expense request/thread/expense correlation across intake, retrieval, rule extraction, source validation, deterministic evaluation, and response persistence; verify INR 6500/7000 remains `COMPLIANT`, INR 9500/7000 remains `NEEDS_REVIEW`, and trace metadata observes rather than chooses those outcomes.
- [x] 3.7 Emit safe deterministic-decision metadata for expense type, rule type, policy limit, decision, confidence, citation count, and abstention category; verify purpose, receipt image/content, and other free text are absent.
- [x] 3.8 Emit `HUMAN_REVIEW_INTERRUPTED` and `WORKFLOW_RESUMED` markers using existing thread/expense/exception/review IDs, status, and action; verify interrupt/resume, more-information, approve, and reject regressions pass without exporting full comments or justification.
- [x] 3.9 Add request-level trace linkage at API/service boundaries and sanitized failure categories for validation, retrieval, reranker, model, citation, workflow-conflict, and database errors; verify HTTP response contracts and retryability remain unchanged.
- [x] 3.10 Audit runtime source for full-state/raw-content export and duplicate tracing; verify targeted source assertions and trace snapshots show only high-value stages and minimized metadata.

## 4. Golden Dataset Contracts and Deterministic Metrics

- [x] 4.1 Define versioned Pydantic-compatible schemas/loaders for Policy Q&A and expense golden datasets; verify malformed fields, duplicate IDs, unsupported decisions, missing relevance judgments, and invalid numeric values fail with case-specific messages.
- [x] 4.2 Extend the Policy Q&A dataset to cover all six synthetic policies, paraphrases, expected policy/section/facts, citation expectations, and abstention while keeping the set manageable; verify schema and source-coverage tests pass.
- [x] 4.3 Extend the expense dataset to cover `COMPLIANT`, `NON_COMPLIANT`, `NEEDS_REVIEW`, and `INSUFFICIENT_INFORMATION`, exact Decimal limits, receipt behavior, source lineage, and travel categories; verify 100% schema coverage and unique IDs.
- [x] 4.4 Implement deterministic Precision@5, Recall@10, and MRR calculations with explicit empty-result/relevance behavior; verify table-driven unit tests cover exact numerators, denominators, rank ties, and no-relevant-evidence cases.
- [x] 4.5 Implement citation correctness and valid-citation coverage using retrieval membership, expected policy/section, and authoritative eligibility results; verify known valid and mismatch cases produce exact scores and categorized failures.
- [x] 4.6 Implement exact deterministic decision accuracy and limit/source checks without an LLM judge; verify all controlled golden cases achieve 1.00 and deliberate regressions identify failing case IDs.
- [x] 4.7 Add configurable deterministic threshold evaluation for Precision@5 >= 0.80, Recall@10 >= 0.90, citation correctness >= 0.95, and decision accuracy = 1.00; verify boundary values pass and sub-threshold values fail with a non-zero runner result.

## 5. Offline Evaluation Runners

- [x] 5.1 Create a credential-free retrieval evaluation runner that loads the golden set, executes selected retrieval composition, calculates deterministic metrics, and writes a versioned JSON report; verify it runs against local PostgreSQL fixtures without model credentials.
- [x] 5.2 Create a deterministic expense-decision runner using controlled rules/evidence and exact assertions; verify it produces per-case results and 1.00 accuracy without model or evaluator credentials.
- [x] 5.3 Implement current-version Ragas dataset conversion and offline metrics for supported faithfulness, answer relevance, context precision/relevance, and context recall; verify conversion tests run credential-free and live evaluation emits an explicit skip report when required credentials are absent.
- [x] 5.4 Implement current-version DeepEval test-case conversion and complementary faithfulness, answer relevance, contextual precision, and contextual recall metrics; verify conversion tests run credential-free and optional evaluator configuration is read only at command execution.
- [x] 5.5 Ensure Ragas and DeepEval imports/clients are absent from FastAPI startup and request modules; verify an application import/startup test succeeds when evaluator dependencies or credentials are unavailable.
- [x] 5.6 Add optional manual LangSmith dataset synchronization/experiment support only if it remains small and version-compatible; otherwise document the deliberate deferral and verify local JSON remains the authoritative evaluation source.

## 6. Retrieval Benchmark and Reports

- [x] 6.1 Implement evaluator-only vector retrieval composition against the golden queries without modifying production configuration; verify returned results retain identifiers/ranks and production settings remain unchanged.
- [x] 6.2 Implement evaluator-only hybrid FTS+vector+RRF composition using the same queries, filters, and expected evidence; verify metric inputs are comparable with vector-only results.
- [x] 6.3 Implement evaluator-only hybrid-plus-reranker composition with explicit unavailable/fallback reporting; verify reranker failure is not mislabeled as reranked quality.
- [x] 6.4 Add a benchmark runner reporting strategy, Precision@5, Recall@10, MRR, per-case results, and average latency; verify all three strategies run over identical case IDs and write `retrieval_benchmark.json`.
- [x] 6.5 Implement report serialization with schema version, timestamp, dataset hash, configuration, dependency/metric versions, aggregates, thresholds, status, case failures, and sanitized errors; verify deterministic JSON output and no secret/raw-content fields.
- [x] 6.6 Generate a concise Markdown summary linking retrieval, decision, citation, benchmark, Ragas, and DeepEval reports, distinguishing pass/fail/skip/baseline states; verify rendering and report-path tests.
- [x] 6.7 Run the local deterministic evaluations and benchmark against the required PostgreSQL corpus, capture actual results, and review whether hybrid/reranking improves quality rather than assuming it does.
- [x] 6.8 Run Ragas and DeepEval only when evaluator credentials are available; record actual baseline scores or explicit credential-based skip evidence without inventing results or thresholds.

## 7. CI and Documentation

- [x] 7.1 Replace the placeholder RAG evaluation workflow with pull-request/push deterministic dataset, metric, decision, benchmark-smoke, and report-artifact steps; verify workflow syntax and that default jobs reference no LangSmith/OpenAI/Ragas/DeepEval secrets.
- [x] 7.2 Add a separate manual or scheduled live-evaluation path guarded by explicit secrets/configuration; verify its absence or skip cannot fail the default deterministic job.
- [x] 7.3 Update README with dependency installation, LangSmith configuration, disabled behavior, runtime metadata boundaries, deterministic evaluation commands, benchmark command, optional Ragas/DeepEval commands, reports, and credential requirements; verify commands are checkout-aware for Windows.
- [x] 7.4 Extend `docs/local-validation.md` with Phase 007 infrastructure, tracing-disabled/mocked/live checks, evaluator skips, deterministic thresholds, benchmark/report expectations, CI behavior, troubleshooting, and OpenSpec verification.
- [x] 7.5 Document why tracing observes but never determines policy, expense, or human-review outcomes and why external evaluation remains offline; verify Phase 008/AWS and production-alerting deferrals are explicit.

## 8. Verification and OpenSpec Completion

- [x] 8.1 Add focused observability tests for redaction, context propagation, disabled/enabled tracing, exporter outage, span hierarchy, metadata minimization, error mapping, and no duplicate model spans; verify all pass without LangSmith network access.
- [x] 8.2 Add focused evaluation tests for dataset validation, deterministic metrics, thresholds, runners, report schemas, optional evaluator skips, and strategy isolation; verify all pass without external model credentials.
- [x] 8.3 Run Phase 003 Policy Q&A regressions and verify grounded answers, retrieval ordering, citation rejection, abstention, and controlled provider failures remain unchanged.
- [x] 8.4 Run Phase 004 expense regressions and verify intake, idempotency, exact Decimal rules, evidence validation, decisions, and persistence remain unchanged.
- [x] 8.5 Run Phase 005 HITL regressions and verify interrupt/resume, concurrency, audit, summary failure, more-information continuation, and human-only finalization remain unchanged.
- [x] 8.6 Run Phase 006 Model Gateway regressions and verify routing, budgets, retries, repair, fallback, guardrails, provider isolation, and sanitized telemetry remain unchanged.
- [x] 8.7 Run the complete backend suite against required PostgreSQL/Redis fixtures and verify every collected test passes with no live LangSmith or evaluator dependency.
- [x] 8.8 Run frontend tests and production build and verify Phase 007 introduces no UI or typed-client regression.
- [x] 8.9 Run secret-signature, direct-SDK, evaluator-import-boundary, staged-file, and whitespace audits; verify no credential, `.env`, raw telemetry content, or unrelated user file enters Phase 007 scope.
- [x] 8.10 Run strict validation for `007-observability-evaluation`, canonical specs, and all OpenSpec content; verify zero failures and align task checkboxes only with completed evidence.
- [x] 8.11 Produce the Phase 007 implementation report with files, dependencies, tracing hierarchy, redaction, datasets, metrics, benchmarks, reports, CI, commands/results, optional evaluator scores/skips, limitations, and explicit Phase 008 deferrals; stop without implementing Phase 008.
