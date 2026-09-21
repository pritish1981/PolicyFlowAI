# PolicyFlow AI

PolicyFlow AI is a production-oriented portfolio proof of concept for enterprise
expense-policy question answering, deterministic compliance assessment, and
controlled human exception review.

It combines FastAPI, React, LangGraph, PostgreSQL with pgvector, hybrid
retrieval, a governed Model Gateway, human-in-the-loop workflows, privacy-safe
tracing, offline evaluation, and an AWS ECS/Fargate deployment definition.

Only synthetic policy and expense data belongs in this project. PolicyFlow AI
is not a production financial authorization system.

## Project status

Phases 001-007 are implemented, validated, synchronized into canonical
OpenSpec specifications, and archived. Phase 008 is implemented and locally
validated with all 41 tasks complete; it remains active until review and
archive.

No AWS resources, Cloudflare records, production secrets, or real deployment
were created by Phase 008.

| Phase | Capability | Status |
|---|---|---|
| 001 | Platform foundation | Complete and archived |
| 002 | Policy ingestion and hybrid RAG | Complete and archived |
| 003 | Grounded Policy Q&A | Complete and archived |
| 004 | Expense compliance assessment | Complete and archived |
| 005 | Human exception review | Complete and archived |
| 006 | Model Gateway and guardrails | Complete and archived |
| 007 | Observability and evaluation | Complete and archived, 56/56 tasks |
| 008 | AWS deployment hardening | Implemented and locally validated, 41/41 tasks; archive and cloud deployment pending |

Current validation evidence:

- Python: 135 tests passed
- Frontend: 2 tests passed and Vite production build passed
- Docker: backend and frontend production images built successfully
- Docker Compose: PostgreSQL, Redis, backend, and frontend healthy
- Local database: pgvector 0.8.6 and Alembic head 20260920_0004
- Terraform: format and provider-backed validation passed with Terraform 1.9.8
- GitHub Actions: workflow YAML and actionlint passed
- OpenSpec: 7 canonical specs passed; repository-wide 8 items passed
- Frontend production dependency audit: 0 vulnerabilities

## Capabilities delivered

### Platform and policy intelligence

- FastAPI backend and React/TypeScript frontend
- PostgreSQL 16, pgvector, Redis, SQLAlchemy, Alembic, and Docker Compose
- Six synthetic policies, POL-001 through POL-006
- Section-aware, content-hash-idempotent policy ingestion
- PostgreSQL full-text search and pgvector semantic retrieval
- Reciprocal Rank Fusion with optional Cohere or local BGE reranking
- Database-backed citation validation and safe abstention

### Expense compliance and human review

- Strict Pydantic request, state, and response contracts
- Exact Decimal amount and receipt rules
- COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, and
  INSUFFICIENT_INFORMATION outcomes
- Durable LangGraph checkpointing in PostgreSQL
- Auditable exception interrupt, resume, rework, and finalization
- Human-only APPROVE, REJECT, and REQUEST_MORE_INFORMATION authority
- Reviewer queue and detail UI

### Model governance and quality

- Provider-neutral Model Gateway with task routing and versioned prompts
- Typed evidence, structured output, bounded retries, repair, and fallback
- Input, evidence, citation, authority, and token-budget guardrails
- Optional fail-open LangSmith tracing with minimized metadata
- Versioned Policy Q&A and expense golden datasets
- Deterministic retrieval, citation, and decision metrics
- Offline Ragas and DeepEval adapters with explicit credential-based skips

### AWS deployment hardening

- Non-root FastAPI image and unprivileged nginx frontend image
- Terraform for a two-AZ VPC, public ALB, and private Fargate services
- Private encrypted RDS PostgreSQL and ElastiCache Redis
- Immutable ECR repositories and SHA-tagged deployments
- Encrypted, versioned, public-access-blocked S3 storage
- Secrets Manager references and separate least-privilege ECS roles
- Separate backend, frontend, and migration CloudWatch log groups
- GitHub OIDC deployment with one-off migration, stability waits, smoke tests,
  and prior-task-definition rollback
- Cloudflare proxied DNS and Full (strict) TLS operating guidance

See the [Phase 008 implementation report](docs/phase-008-implementation-report.md)
for the full inventory and validation evidence.

## Architecture

    User
      |
      v
    Cloudflare - DNS, TLS, edge controls
      |
      v
    AWS Application Load Balancer
      |
      +--> React/nginx frontend - ECS/Fargate
      |
      +--> FastAPI backend - ECS/Fargate
              |
              +--> RDS PostgreSQL
              |      +--> app business records
              |      +--> rag documents, FTS, and pgvector
              |      +--> audit records
              |      +--> LangGraph checkpoints
              |
              +--> ElastiCache Redis - transient coordination only
              +--> S3 - synthetic policy sources and optional artifacts
              +--> OpenAI/Cohere over outbound HTTPS
              +--> LangSmith over outbound HTTPS

    GitHub Actions -> Amazon ECR -> migration task -> ECS services
    ECS logs -> CloudWatch
    AI trace metadata -> optional LangSmith

For local development, Docker Compose provides PostgreSQL, Redis, backend, and
frontend equivalents.

## Authority and safety boundaries

- PostgreSQL policy documents and chunks are the authoritative evidence source.
- Only ACTIVE and effective evidence may support a grounded answer.
- Models may extract and summarize; they do not authorize financial outcomes.
- Deterministic code selects compliance outcomes from validated evidence.
- Material answers without valid citations become safe abstentions.
- Only an authorized human reviewer may approve or reject an exception.
- LangGraph checkpoints are execution state, not business truth.
- Redis is transient and never stores authoritative business or checkpoint data.
- Observability and evaluation never determine application outcomes.
- No environment file, API key, database password, Terraform state, or private
  policy document may be committed.

## Technology stack

- Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic
- Workflow: LangGraph with PostgreSQL checkpoints
- Data: PostgreSQL 16, pgvector, Redis
- Retrieval: PostgreSQL FTS, pgvector, RRF, Cohere/BGE adapters
- Models: governed provider-neutral gateway with an OpenAI adapter
- Frontend: React 18, TypeScript, Vite, Vitest, nginx
- Observability: structured logs, CloudWatch, optional LangSmith
- Evaluation: Pytest, deterministic metrics, Ragas, DeepEval
- Delivery: Docker Compose, Terraform, GitHub Actions OIDC, ECR, ECS/Fargate
- Edge: Cloudflare and an ACM-backed AWS ALB

## Repository layout

    backend/                    FastAPI application, workflows, rules, migrations, tests
    frontend/                   React UI, tests, and production nginx configuration
    policies/synthetic/         Synthetic policy source documents
    scripts/                    Ingestion, evaluation, seeding, and deployment smoke tools
    evaluation/                 Golden datasets, metrics, runners, and ignored reports
    infrastructure/terraform/   AWS Terraform root
    infrastructure/aws/         AWS component operating notes
    infrastructure/cloudflare/  Edge DNS and TLS guidance
    openspec/specs/             Canonical capability specifications
    openspec/changes/           Active and archived OpenSpec changes
    docs/local-validation.md    Detailed Phase 001-008 local validation
    docs/aws-deployment.md      AWS bootstrap, deployment, rollback, cost, and cleanup

## Local prerequisites

- Docker Desktop with the Linux container engine running
- Python 3.12
- uv
- Node.js 20 and npm
- PowerShell
- Terraform 1.8-1.x only for direct local IaC commands

Provider and tracing credentials are optional for automated validation. Real
model-backed Q&A requires an OpenAI key; Cohere reranking requires a Cohere key.

## Local environment

The repository intentionally does not publish an environment template. Create a
private .env file locally with at least:

    POSTGRES_DB=policyflow
    POSTGRES_USER=policyflow
    POSTGRES_PASSWORD=<private-local-password>
    POSTGRES_PORT=5433
    CORS_ORIGINS=http://localhost:5173
    VITE_API_BASE_URL=http://localhost:8000

Optional private settings include OPENAI_API_KEY, COHERE_API_KEY,
POLICY_ADMIN_TOKEN, LANGSMITH_API_KEY, and provider/model selections.

Host processes connect to PostgreSQL on localhost:5433. Containers connect to
postgres:5432. Redis is available locally on port 6379.

## Quick start with Docker Compose

From the repository root:

    docker compose config --quiet
    docker compose up -d --build
    docker compose ps

Compose applies Alembic migrations before starting its single local backend.
Wait until all four services report healthy, then open:

- Frontend: http://localhost:5173
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Liveness: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

Validate dependencies:

    docker compose exec -T postgres pg_isready -U policyflow -d policyflow
    docker compose exec -T redis redis-cli ping
    Invoke-RestMethod http://localhost:8000/health
    Invoke-RestMethod http://localhost:8000/ready

Expected readiness reports PostgreSQL and Redis ready.

## Database migrations and policy ingestion

For host-run migrations:

    Push-Location backend
    uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
    uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
    Pop-Location

Expected head:

    20260920_0004

Ingest the synthetic policy corpus:

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py

The baseline corpus contains six ACTIVE policy documents and 50 chunks.
Re-ingestion is content-hash idempotent.

## Local validation

Run the complete Python suite:

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q tests backend/tests

Latest result:

    135 passed

Run frontend tests and build:

    Push-Location frontend
    npm.cmd test -- --run
    npm.cmd run build
    npm.cmd audit --omit=dev
    Pop-Location

Latest result:

    2 tests passed
    Vite production build passed
    0 production dependency vulnerabilities

Build the production images:

    docker build -f backend/Dockerfile -t policyflow-backend:local .
    docker build -t policyflow-frontend:local frontend

Validate Terraform without creating AWS resources:

    terraform -chdir=infrastructure/terraform fmt -check
    terraform -chdir=infrastructure/terraform init -backend=false
    terraform -chdir=infrastructure/terraform validate

If Terraform is not installed, use the documented Docker-based validation in
[local validation](docs/local-validation.md).

## Primary APIs

Policy Q&A:

- POST /api/v1/policy/query
- Returns GROUNDED only with verified citations
- Safely returns INSUFFICIENT_INFORMATION when evidence is inadequate

Expense compliance:

- POST /api/v1/expenses
- GET /api/v1/expenses/{expense_id}
- POST /api/v1/expenses/{expense_id}/clarifications

Exception and review:

- POST /api/v1/expenses/{expense_id}/exceptions
- POST /api/v1/exceptions/{exception_id}/information
- GET /api/v1/reviews/pending
- GET /api/v1/reviews/{exception_id}
- POST /api/v1/reviews/{exception_id}/decision

Synthetic demo authorization uses X-Demo-Role: EMPLOYEE for employee actions
and X-Demo-Role: REVIEWER with optional X-Demo-User for reviewer actions.

## Evaluation and tracing

Deterministic evaluation:

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_retrieval --strategy hybrid
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_decisions
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.benchmark

Recorded Phase 007 gates:

| Metric | Required | Recorded |
|---|---:|---:|
| Precision at 5 | at least 0.80 | 0.9091 |
| Recall at 10 | at least 0.90 | 0.9091 |
| MRR | reported | 0.9091 |
| Citation correctness | at least 0.95 | 1.0000 |
| Valid-citation coverage | reported | 1.0000 |
| Decision accuracy | exactly 1.00 | 1.0000 |

Ragas and DeepEval are optional offline baselines. With evaluation disabled or
credentials absent, their runners produce an explicit SKIP report. Generated
reports stay under evaluation/reports and are ignored except for .gitkeep.

LangSmith tracing is disabled by default and fails open. Exported metadata is
bounded and excludes raw prompts, policy bodies, expense purpose, justification,
reviewer comments, credentials, database URLs, provider payloads, and graph
state.

## OpenSpec

Validate the active change and complete repository:

    npx.cmd -y @fission-ai/openspec@1.10.0 validate 008-aws-deployment-hardening --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 list --json

Current expected state:

- Phase 008: valid and 41/41 tasks complete
- Canonical specs: 7 passed, 0 failed
- Repository-wide: 8 passed, 0 failed
- One active change: 008-aws-deployment-hardening
- Phase 008 is ready for review and archive

## AWS deployment boundary

The repository defines deployment artifacts but has not deployed them.

A real deployment requires:

- approved AWS account, region, and cost budget;
- remote Terraform state and GitHub OIDC bootstrap;
- Cloudflare-managed hostname and regional ACM certificate;
- privately populated Secrets Manager values;
- reviewed Terraform plan and explicit apply approval;
- post-apply RDS pgvector, ECS, ALB, CloudWatch, rollback, and public smoke
  validation.

Follow the [AWS deployment runbook](docs/aws-deployment.md). Never run
Terraform apply or destroy without reviewing the exact plan and target account.

## CI/CD behavior

Pull-request and push CI runs:

- pgvector PostgreSQL and Redis service containers;
- Alembic migrations and the complete Python suite;
- frontend tests and production build;
- strict OpenSpec validation;
- Terraform format and validation;
- backend and frontend Docker builds;
- deterministic evaluation gates and report artifacts.

The protected manual AWS workflow uses GitHub OIDC and requires the confirmation
value DEPLOY. It builds Git-SHA images, publishes them to ECR, runs a dedicated
migration task, updates ECS services, waits for stability, runs public smoke
validation, and restores prior task definitions after failure.

## Troubleshooting

- Docker API unavailable: start Docker Desktop and select Linux containers.
- PostgreSQL connection failure: host processes use port 5433, not 5432.
- Readiness returns 503: inspect PostgreSQL and Redis container health.
- Stale database schema: run Alembic upgrade head from backend.
- Empty retrieval: ingest the six-policy synthetic corpus.
- Policy Q&A returns 503: configure a private OpenAI key for real generation.
- Reranker fallback: configure Cohere/local BGE or interpret results as fallback.
- Evaluator reports SKIP: explicitly enable evaluation and provide credentials.
- First local embedding or BGE run: allow time for model download.
- Windows checkpoint errors: retain the documented SelectorEventLoop
  worker-thread path for psycopg under Uvicorn.
- Terraform validate cannot find providers: run init -backend=false first.

## Documentation

- [Detailed local validation](docs/local-validation.md)
- [AWS deployment and operations](docs/aws-deployment.md)
- [Phase 008 implementation report](docs/phase-008-implementation-report.md)
- [Phase 007 implementation report](docs/phase-007-implementation-report.md)
- [Functional requirements](docs/architecture/PolicyFlow_AI_FRD_v1.0.docx)
- [High-level design](docs/architecture/PolicyFlow_AI_HLD_v1.0.docx)
- [Low-level design](docs/architecture/PolicyFlow_AI_LLD_v1.0.docx)
- [Project structure](docs/architecture/PolicyFlowAI-project-structure.md)

## Remaining production scope

Phase 008 intentionally does not provide enterprise SSO/RBAC, multi-region
active-active deployment, sophisticated autoscaling, automated disaster
recovery, mandatory Cloudflare authenticated origin pulls, complex blue/green
orchestration, or real-cloud evidence before an authorized deployment.
