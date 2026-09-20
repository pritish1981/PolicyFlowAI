## Why

PolicyFlow AI currently emits useful local structured logs and governed Model Gateway metadata, but engineers cannot follow a request across LangGraph, retrieval, generation, deterministic validation, and human review as one privacy-safe trace. The repository also has golden datasets but no executable quality metrics or regression reports, so retrieval and RAG changes cannot be measured consistently before release.

## What Changes

- Add optional LangSmith runtime tracing for business-relevant API, LangGraph, retrieval, Model Gateway, citation, deterministic-decision, and HITL stages while preserving local structured logging and fail-open business execution when tracing is disabled or unavailable.
- Reuse request, thread, expense, exception, and review identifiers for end-to-end correlation; add centralized metadata minimization, allow-listing, redaction, duration, and normalized error categorization without exporting raw prompts, policy bodies, justifications, secrets, or provider payloads.
- Extend the existing Policy Q&A and expense golden datasets and define stable schemas for expected evidence, facts, citations, and exact deterministic decisions.
- Add credential-free deterministic retrieval, citation, and decision metrics plus vector-only, hybrid, and hybrid-plus-reranker benchmarking against identical cases.
- Add offline Ragas and DeepEval runners that use current supported APIs, remain separate from request execution, establish baselines before enforcing external-judge thresholds, and skip safely when optional evaluator credentials are absent.
- Generate machine-readable JSON and human-readable summary reports and add a CI workflow that gates deterministic regressions without requiring live LangSmith, OpenAI, Ragas, or DeepEval calls.
- Document local tracing, evaluation, benchmark, report, and CI workflows, including which optional commands require external credentials.
- Keep AWS/CloudWatch infrastructure, Prometheus/Grafana, production alerting, new business flows, new retrieval algorithms/providers/databases, confidential telemetry, and Phase 008 deployment out of scope.

## Capabilities

### New Capabilities

- `observability-evaluation`: Configurable privacy-safe runtime tracing and reproducible offline quality evaluation for PolicyFlow AI workflows.

### Modified Capabilities

None. Existing model-governance, retrieval, policy-answer, expense-decision, and exception-review authority contracts remain unchanged; this capability observes and evaluates them without changing their behavior.

## Impact

- **Runtime:** `backend/app/observability/`, selected API/service/graph/RAG/rules/HITL instrumentation points, and safe configuration in `backend/app/core/config.py`.
- **Dependencies:** compatible pinned ranges for LangSmith, Ragas, and DeepEval; all external tracing/evaluation remains optional at runtime and in default CI.
- **Evaluation:** golden datasets, deterministic metrics, offline runners, benchmarks, report artifacts, and credential-free tests under `evaluation/` and `backend/tests/`.
- **CI and documentation:** `.github/workflows/rag-evaluation.yml`, `README.md`, and consolidated local validation guidance.
- **Compatibility:** no API response contract, deterministic expense result, citation authority, persisted business truth, or human-review authorization changes.
