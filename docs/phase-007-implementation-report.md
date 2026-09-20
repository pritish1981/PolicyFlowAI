# Phase 007 Implementation Report

## Outcome

Phase 007 adds optional privacy-safe LangSmith tracing and reproducible offline
evaluation without changing API contracts, retrieval algorithms, deterministic
expense authority, citation authority, checkpoint behavior, or human-review
authorization. Runtime tracing is fail-open. Ragas and DeepEval remain offline.
Phase 008 was not started.

## Dependencies and configuration

Resolved on Python 3.12:

- langsmith 0.13.0, declared as langsmith>=0.13,<0.14
- ragas 0.3.9, declared as ragas>=0.3.9,<0.4
- deepeval 3.9.9, declared as deepeval>=3.9,<4.0

New settings cover disabled-by-default tracing, optional endpoint/project/key,
offline-evaluation enablement, dataset/report paths, and deterministic thresholds.
The ignored local .env.example was updated with placeholders only; it remains
excluded by the repository publication rule.

## Runtime tracing architecture

Policy Q&A and expense service boundaries create an immutable TraceContext from
existing request/thread/business IDs. High-value LangGraph nodes use project-owned
stage spans. A context-local parent run links nested stages without making global
mutable state authoritative.

The trace hierarchy covers:

- Policy Q&A request, validation, filters, hybrid retrieval, RRF, reranking,
  governed generation, citation validation, and final response
- Expense request, intake, evidence retrieval, rule extraction, source
  validation, deterministic decision, and persistence mapping
- Exception context, human-review interrupt, authorized resume, and finalization
- One governed Model Gateway success/failure event per gateway invocation

LangSmith SDK construction exists only in the observability adapter. Disabled,
missing-key, initialization-failure, and exporter-outage paths continue with
sanitized local logs and never alter caller results.

## Privacy and authority

Central metadata allow-listing retains identifiers, counts, ranks, bounded scores,
versions, categories, durations, token usage, retry/fallback state, and outcomes.
It excludes credentials, headers, connection strings, raw questions/prompts,
policy bodies, provider payloads, purpose, justification, reviewer comments,
exception free text, and full graph state. Strings and lists are bounded before
export.

Tracing only observes. PostgreSQL evidence eligibility, deterministic Decimal
rules, citation validation, persisted business state, and authorized human
actions remain authoritative.

## Golden datasets and metrics

The Policy Q&A dataset contains 11 versioned cases covering all six synthetic
policies, paraphrases, expected policy/section/facts, and one unsupported request.
The expense dataset contains 10 versioned cases covering COMPLIANT,
NON_COMPLIANT, NEEDS_REVIEW, INSUFFICIENT_INFORMATION, exact limits, receipt
behavior, source lineage, and domestic/international travel.

Pure deterministic metrics implement Precision@5, Recall@10, MRR, citation
correctness, valid-citation coverage, exact decision accuracy, and configurable
threshold gates. Dataset loaders reject malformed cases, duplicate IDs,
unsupported decisions, absent relevance judgments, and invalid numbers with
case-specific messages.

## Evaluation runners and reports

Credential-free runners provide:

- live PostgreSQL hybrid retrieval and database-eligible citation evaluation
- exact deterministic expense-decision evaluation
- evaluator-only vector, hybrid RRF, and hybrid-plus-reranker benchmark
- versioned JSON report serialization and a Markdown report index

Ragas and DeepEval convert the authoritative local dataset without importing
their packages into FastAPI. Disabled or missing-credential runs write explicit
skip reports. When enabled, an operator supplies a generated answer/context JSON
bundle through --results; the runners execute current-version judge metrics and
record baseline scores without enforcing an unapproved external threshold.
LangSmith dataset synchronization is deliberately deferred; local JSON remains
authoritative.

Generated local reports:

- evaluation/reports/retrieval_evaluation.json
- evaluation/reports/citation_evaluation.json
- evaluation/reports/expense_decisions.json
- evaluation/reports/retrieval_benchmark.json
- evaluation/reports/ragas.json
- evaluation/reports/deepeval.json
- evaluation/reports/SUMMARY.md

These timestamped/latency-bearing reports are ignored build artifacts, not source
files.

## Actual local results

Docker evidence:

- PostgreSQL and Redis healthy
- Alembic head 20260920_0004
- 6 ACTIVE documents and 50 chunks

Deterministic evaluation:

- hybrid Precision@5: 0.9090909091
- hybrid Recall@10: 0.9090909091
- hybrid MRR: 0.9090909091
- citation correctness: 1.0
- valid-citation coverage: 1.0
- deterministic decision accuracy: 1.0

Benchmark:

| Strategy | Precision@5 | Recall@10 | MRR | Average latency |
|---|---:|---:|---:|---:|
| vector | 0.9091 | 0.9091 | 0.9091 | 185.26 ms |
| hybrid | 0.9091 | 0.9091 | 0.9091 | 50.52 ms |
| hybrid+rerank | 0.9091 | 0.9091 | 0.9091 | 58.23 ms |

The hybrid and vector quality scores tied in this local run; hybrid was faster.
The hybrid+rerank arm used the deliberately unavailable evaluator reranker and is
correctly labeled fallback. No genuine reranker improvement is claimed.

Ragas and DeepEval recorded SKIP because live external evaluation was disabled.
No score or threshold was invented.

Regression evidence:

- focused Phase 007 and Policy Q&A: 44 passed
- complete backend: 116 passed
- frontend: 2 tests passed
- Vite production build: passed
- workflow YAML parse: passed
- OpenSpec change validation: valid
- canonical OpenSpec validation: 6 passed, 0 failed
- all OpenSpec validation: 7 passed, 0 failed
- credential-signature audit: clean
- runtime evaluator-import audit: clean
- direct OpenAI SDK audit: adapter only
- git diff whitespace audit: no errors; line-ending notices only

## CI

The RAG evaluation workflow now runs credential-free dataset, metric, tracing,
decision, optional-evaluator-skip, report, and benchmark-smoke checks for pull
requests and main-branch pushes. It uploads report artifacts. A separate guarded
workflow-dispatch job references the optional external evaluator secret; default
jobs do not.

## Files created for Phase 007

- backend/app/observability/context.py
- backend/app/observability/contracts.py
- backend/app/observability/redaction.py
- backend/tests/test_observability.py
- backend/tests/test_evaluation.py
- evaluation/__init__.py
- evaluation/models.py
- evaluation/metrics.py
- evaluation/reporting.py
- evaluation/retrieval.py
- evaluation/run_retrieval.py
- evaluation/run_decisions.py
- evaluation/benchmark.py
- evaluation/summarize.py
- docs/phase-007-implementation-report.md
- openspec/specs/observability-evaluation/spec.md
- openspec/changes/archive/2026-09-20-007-observability-evaluation/proposal.md
- openspec/changes/archive/2026-09-20-007-observability-evaluation/design.md
- openspec/changes/archive/2026-09-20-007-observability-evaluation/specs/observability-evaluation/spec.md
- openspec/changes/archive/2026-09-20-007-observability-evaluation/tasks.md

## Files updated for Phase 007

- .github/workflows/rag-evaluation.yml
- README.md
- backend/requirements.txt
- backend/app/core/config.py
- backend/app/graph/graph.py
- backend/app/graph/expense_graph.py
- backend/app/observability/tracing.py
- backend/app/observability/metrics.py
- backend/app/services/policy_service.py
- backend/app/services/expense_service.py
- backend/app/services/exception_service.py
- backend/tests/test_policy_qa.py
- evaluation/datasets/policy_qa_golden.json
- evaluation/datasets/expense_cases.json
- evaluation/ragas/evaluate_rag.py
- evaluation/deepeval/evaluate_agent.py
- docs/local-validation.md
- local ignored .env.example placeholder template

## Known limitations and Phase 008 deferrals

- Live LangSmith visual verification requires an operator-owned key and was not
  performed during credential-free validation.
- Ragas/DeepEval paid baselines require explicit enablement, credentials, and a
  generated answer/context bundle.
- Genuine reranker benchmarking requires an explicitly configured local BGE or
  authorized Cohere evaluator.
- AWS/CloudWatch, Prometheus/Grafana, production dashboards/alerts, durable cost
  accounting, new retrieval systems, and deployment hardening remain deferred.
