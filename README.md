# PolicyFlow AI

PolicyFlow AI is a production-oriented proof of concept for enterprise expense
compliance, policy question answering, and controlled human exception review.
It combines FastAPI, React, LangGraph, PostgreSQL/pgvector, deterministic
business rules, a governed Model Gateway, privacy-safe tracing, and offline
quality evaluation.

The repository uses synthetic policy and expense data. It is not a production
financial authorization system.

## Current status

Phases 001 through 007 are implemented, validated, synchronized into canonical
OpenSpec specifications, and archived. There are currently no active OpenSpec
changes. Phase 008 has not started.

| Phase | Capability | Status |
|---|---|---|
| 001 | Platform foundation | Complete and archived |
| 002 | Policy ingestion and hybrid RAG | Complete and archived |
| 003 | Policy Q&A | Complete and archived |
| 004 | Expense compliance assessment | Complete and archived |
| 005 | Human exception review | Complete and archived |
| 006 | Model Gateway and guardrails | Complete and archived |
| 007 | Observability and evaluation | Complete and archived, 56/56 tasks |

Canonical specifications are under [openspec/specs](openspec/specs/). Archived
change artifacts are under [openspec/changes/archive](openspec/changes/archive/).

## Completed phases

### Phase 001 — Platform foundation

- FastAPI backend and React/TypeScript/Vite frontend
- PostgreSQL 16 with pgvector and Redis
- SQLAlchemy, Alembic, Docker Compose, health/readiness endpoints, and CI
- Deterministic application boundaries and synthetic-data foundation

[Archived change](openspec/changes/archive/2026-09-13-001-platform-foundation/)

### Phase 002 — Policy ingestion and hybrid RAG

- Six synthetic policies, POL-001 through POL-006
- Section-aware parsing and content-hash idempotent ingestion
- PostgreSQL full-text search and pgvector retrieval
- ACTIVE/effective-date, category, region, and travel filters
- Reciprocal Rank Fusion and Cohere/BGE reranker adapters
- Authoritative policy/chunk persistence and citation lookup

[Archived change](openspec/changes/archive/2026-09-13-002-policy-ingestion-and-hybrid-rag/)

### Phase 003 — Policy Q&A

- Strict question and grounded-answer contracts
- LangGraph Policy Q&A workflow
- Hybrid retrieval, RRF, optional reranking, and safe abstention
- Structured model output through the governed gateway
- Database-backed citation and source validation
- React question-and-citation experience

[Canonical spec](openspec/specs/policy-qa/spec.md) ·
[Archived change](openspec/changes/archive/2026-09-17-003-policy-qa/)

### Phase 004 — Expense compliance assessment

- Structured expense intake, clarification, and idempotency
- Separate expense and assessment persistence
- Evidence-grounded rule extraction
- Exact Decimal amount and receipt evaluation
- COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, and
  INSUFFICIENT_INFORMATION outcomes
- React expense assessment experience

[Canonical spec](openspec/specs/expense-compliance/spec.md) ·
[Archived change](openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/)

### Phase 005 — Human exception review

- Durable exception workflow with PostgreSQL LangGraph checkpoints
- Human-only APPROVE, REJECT, and REQUEST_MORE_INFORMATION actions
- Auditable interrupt, resume, rework, and finalization lifecycle
- Deterministic variance calculation
- Non-authoritative AI review summaries
- Reviewer queue and detail UI

The persisted human action is authoritative. AI summaries and checkpoints are
not business truth, and the original expense assessment remains auditable.

[Canonical spec](openspec/specs/exception-review/spec.md) ·
[Archived change](openspec/changes/archive/2026-09-20-005-exception-hitl/)

### Phase 006 — Model Gateway and guardrails

- One provider-neutral gateway for Policy Q&A, expense-rule extraction, and
  exception-summary generation
- Task routing, versioned prompts, typed evidence, and structured output
- Input/output limits and request/thread token budgets
- Bounded technical retries, one schema-repair attempt, and optional technical
  fallback
- Input, evidence, citation, and authority guardrails
- Sanitized provider-neutral model telemetry

The gateway does not replace PostgreSQL evidence checks, deterministic expense
rules, citation authority, or human review authorization.

[Canonical spec](openspec/specs/model-governance/spec.md) ·
[Archived change](openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/)

### Phase 007 — Observability and evaluation

- Optional fail-open LangSmith tracing behind a project-owned adapter
- Immutable request, thread, expense, exception, and review correlation
- High-value spans for API/service boundaries, LangGraph nodes, retrieval, RRF,
  reranking, Model Gateway, citation checks, deterministic decisions, and HITL
- Central metadata allow-listing, normalization, bounding, and redaction
- Versioned Policy Q&A and expense golden datasets
- Deterministic Precision@5, Recall@10, MRR, citation correctness,
  valid-citation coverage, and exact decision accuracy
- Vector-only, hybrid, and hybrid-plus-reranker benchmarking
- Optional offline Ragas and DeepEval baselines
- JSON/Markdown reports and credential-free default CI gates

Tracing observes workflows but never determines a policy answer, expense
decision, or reviewer action. Exporter failure cannot change application
results, persistence, checkpoints, or human authority.

[Canonical spec](openspec/specs/observability-evaluation/spec.md) ·
[Archived change](openspec/changes/archive/2026-09-20-007-observability-evaluation/) ·
[Implementation report](docs/phase-007-implementation-report.md)

## End-to-end architecture

    React
      |
      v
    FastAPI and strict Pydantic contracts
      |
      v
    Application services
      |
      v
    LangGraph workflows
      |
      +--> PostgreSQL FTS and pgvector retrieval
      +--> RRF and optional reranking
      +--> governed Model Gateway
      +--> authoritative citation validation
      +--> deterministic Decimal expense rules
      +--> durable human-review interrupt/resume
      |
      v
    PostgreSQL business records and checkpoints

    Runtime observation: local structured logs and optional LangSmith traces
    Offline quality: golden datasets, Pytest, Ragas, DeepEval, and reports

## Authority boundaries

- Policy documents and chunks stored in PostgreSQL are the evidence source.
- Only ACTIVE and effective evidence may support grounded output.
- Models may extract or summarize; they do not authorize financial outcomes.
- Deterministic code selects expense decisions from verified rules.
- A material policy answer without valid citations becomes a safe abstention.
- Only an authorized human reviewer can approve or reject an exception.
- Observability metadata is diagnostic and never business truth.
- Ragas and DeepEval run offline, never during API startup or request handling.

## Technology stack

- Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic
- Workflow: LangGraph with PostgreSQL checkpoints
- Data: PostgreSQL 16, pgvector, Redis
- Retrieval: PostgreSQL FTS, pgvector, RRF, optional Cohere/BGE reranking
- Models: provider-neutral Model Gateway with an OpenAI adapter
- Frontend: React 18, TypeScript, Vite, Vitest
- Observability: structured logs and optional LangSmith
- Evaluation: Pytest, deterministic metrics, Ragas, DeepEval
- Delivery: Docker Compose and GitHub Actions

## Repository layout

    backend/                 FastAPI application, workflows, rules, and tests
    frontend/                React application and UI tests
    policies/synthetic/      Synthetic policy source documents
    scripts/                 Ingestion and smoke utilities
    evaluation/              Golden datasets, metrics, runners, and reports
    openspec/specs/          Canonical capability specifications
    openspec/changes/archive Archived planning/design/task artifacts
    docs/local-validation.md Detailed Phase 001–007 local runbook

## Prerequisites

- Docker Desktop with the Docker engine running
- Python 3.12
- uv
- Node.js 20 and npm
- PowerShell for the commands below

Model and observability credentials are optional for automated validation.
Never commit .env, API keys, database passwords, or production data.

## Environment setup

From the repository root:

    if (-not (Test-Path .env)) { Copy-Item .env.example .env }

Review these local settings:

- Host processes use PostgreSQL at localhost:5433.
- Containers use postgres:5432.
- Redis is exposed at localhost:6379.
- OPENAI_API_KEY is needed only for real model-backed API calls.
- COHERE_API_KEY is needed only for the Cohere reranker.
- RERANK_PROVIDER may be cohere, bge, or rrf.
- LANGSMITH_TRACING defaults to false.
- ENABLE_AI_EVALUATION defaults to false.

The local environment template is intentionally ignored by Git under the
repository's environment-file publication rule.

## Quick start

### 1. Start infrastructure

    docker compose up -d postgres redis
    docker compose ps
    docker compose exec -T postgres pg_isready -U policyflow -d policyflow
    docker compose exec -T redis redis-cli ping

PostgreSQL and Redis should report healthy/ready.

### 2. Apply migrations

    Push-Location backend
    uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
    uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
    Pop-Location

Expected head:

    20260920_0004

### 3. Ingest the synthetic policy corpus

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py

The current corpus contains six ACTIVE documents and 50 chunks. Re-running
ingestion should report unchanged content rather than create duplicates.

### 4. Run backend tests

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests

Latest validated result:

    116 passed

The suite includes unit, API, graph, PostgreSQL integration, HITL, gateway,
observability, dataset, metric, runner, and report coverage. No live LangSmith,
OpenAI, Ragas, or DeepEval call is required.

### 5. Run frontend tests and build

    Push-Location frontend
    npm.cmd test -- --run
    npm.cmd run build
    Pop-Location

Latest validated result:

    2 tests passed
    Vite production build passed

### 6. Start the applications

Backend:

    Push-Location backend
    uv run --no-project --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Frontend, in another terminal:

    Push-Location frontend
    $env:VITE_API_BASE_URL = "http://localhost:8000"
    npm.cmd run dev -- --host localhost

Open:

- Frontend: http://localhost:5173
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

## Primary API surfaces

### Policy Q&A

- POST /api/v1/policy/query
- Returns GROUNDED only with verified citations
- Returns a fixed INSUFFICIENT_INFORMATION response when support is inadequate

### Expenses

- POST /api/v1/expenses
- GET /api/v1/expenses/{expense_id}
- POST /api/v1/expenses/{expense_id}/clarifications

### Exception and review

- POST /api/v1/expenses/{expense_id}/exceptions
- POST /api/v1/exceptions/{exception_id}/information
- GET /api/v1/reviews/pending
- GET /api/v1/reviews/{exception_id}
- POST /api/v1/reviews/{exception_id}/decision

The demo authorization headers are X-Demo-Role: EMPLOYEE for employee actions
and X-Demo-Role: REVIEWER with optional X-Demo-User for reviewer actions.

## Phase 007 evaluation

Keep PostgreSQL running and the policy corpus ingested.

### Deterministic retrieval, citation, and decision gates

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_retrieval --strategy hybrid
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_decisions

Configured gates:

| Metric | Gate | Recorded result |
|---|---:|---:|
| Precision@5 | at least 0.80 | 0.9091 |
| Recall@10 | at least 0.90 | 0.9091 |
| MRR | reported | 0.9091 |
| Citation correctness | at least 0.95 | 1.0000 |
| Valid-citation coverage | reported | 1.0000 |
| Decision accuracy | exactly 1.00 | 1.0000 |

### Retrieval benchmark

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.benchmark

Recorded local results:

| Strategy | Precision@5 | Recall@10 | MRR | Average latency | Interpretation |
|---|---:|---:|---:|---:|---|
| Vector-only | 0.9091 | 0.9091 | 0.9091 | 185.26 ms | measured |
| Hybrid | 0.9091 | 0.9091 | 0.9091 | 50.52 ms | measured |
| Hybrid plus reranker | 0.9091 | 0.9091 | 0.9091 | 58.23 ms | fallback |

Vector and hybrid quality tied in this run. The reranker arm used the deliberate
unavailable-reranker fallback, so no reranking quality improvement is claimed.
Latency is environment-specific and is not a permanent threshold.

### Optional Ragas and DeepEval baselines

    $env:ENABLE_AI_EVALUATION = "false"
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.ragas.evaluate_rag
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.deepeval.evaluate_agent
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.summarize

With evaluation disabled or credentials absent, both external evaluators write
an explicit SKIP report and exit successfully. An enabled live baseline requires
a private evaluator credential and a generated answer/context JSON bundle passed
with --results. External scores remain baselines until thresholds are separately
reviewed and approved.

Generated reports are written under evaluation/reports and ignored by Git except
for .gitkeep because timestamps and latency are environment-specific.

## Optional LangSmith tracing

Configure privately:

    LANGSMITH_TRACING=true
    LANGSMITH_API_KEY=<private key>
    LANGSMITH_PROJECT=policyflow-ai-local
    LANGSMITH_ENDPOINT=https://api.smith.langchain.com

When disabled, missing credentials, or unavailable, the application continues
with sanitized local structured logs. Exported metadata may include existing
correlation IDs, stage names, counts, ranks, scores, model route/usage,
durations, outcomes, and normalized errors.

Exported metadata excludes full prompts/questions, policy bodies, expense
purpose, justification, reviewer comments, authorization data, database
connection secrets, raw provider payloads, and complete graph state.

## OpenSpec validation

    npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 list --json

Expected state:

- 7 canonical specs passed, 0 failed
- 7 total OpenSpec items passed, 0 failed
- no active changes
- Phase 007 archived with 56/56 tasks complete

## CI behavior

The standard CI workflow runs backend and frontend validation. The RAG
evaluation workflow runs credential-free tracing, dataset, metric, decision,
report, optional-evaluator-skip, and benchmark-smoke checks and uploads report
artifacts. It does not require LangSmith or model credentials.

Live external evaluation is a separately guarded manual workflow path.

## Troubleshooting

- Docker API unavailable: start Docker Desktop.
- PostgreSQL connection failure: host processes use port 5433, not 5432.
- Readiness returns 503: inspect PostgreSQL and Redis container health.
- Missing tables or stale schema: run Alembic upgrade head from backend.
- Empty retrieval results: verify six ACTIVE documents and 50 chunks exist.
- First embedding/BGE run is slow: the configured model may be downloaded.
- Policy Q&A returns 503: configure OPENAI_API_KEY for real generation or use
  credential-free automated tests.
- Reranker fallback appears: configure the selected reranker or treat the run as
  fallback quality, not genuine reranked quality.
- Live evaluator reports SKIP: explicitly enable evaluation, configure the
  evaluator credential, and provide a --results bundle.
- Windows async checkpoint issues: retain the documented SelectorEventLoop
  worker-thread path for psycopg under Uvicorn.

## Documentation

- [Consolidated local validation](docs/local-validation.md)
- [Phase 007 implementation report](docs/phase-007-implementation-report.md)
- [Functional requirements](docs/architecture/PolicyFlow_AI_FRD_v1.0.docx)
- [High-level design](docs/architecture/PolicyFlow_AI_HLD_v1.0.docx)
- [Low-level design](docs/architecture/PolicyFlow_AI_LLD_v1.0.docx)
- [Project structure](docs/architecture/PolicyFlowAI-project-structure.md)

## Deferred scope

Phase 008 and later may address AWS deployment hardening, CloudWatch,
production dashboards and alerting, SSO/RBAC hardening, durable cost accounting,
notifications, and other production controls. Phase 007 does not implement
those capabilities.
