# PolicyFlow AI

PolicyFlow AI is an **Enterprise Expense Compliance and Exception Agent** proof of concept. The current application answers policy questions and assesses structured expenses against verified policy evidence.

The [FRD](docs/requirements/PolicyFlow_AI_FRD_v1.0.docx), [HLD](docs/architecture/PolicyFlow_AI_HLD_v1.0.docx), and [LLD](docs/architecture/PolicyFlow_AI_LLD_v1.0.docx) define the broader target. Phase 004 is implemented and its OpenSpec change is archived; the working-tree changes have not been committed or published. Follow the [Phase 004 local validation guide](docs/phase-004-local-validation.md) for current commands and expected results. The Phase 003 runbook below is historical and retains its Phase 003 baselines.

## Current implementation status

- **Phase 001 - Platform foundation:** FastAPI, React/TypeScript/Vite, PostgreSQL 16 with pgvector, Redis, SQLAlchemy, Alembic, health/readiness probes, Docker Compose, and CI foundation. Archived under [`2026-09-13-001-platform-foundation`](openspec/changes/archive/2026-09-13-001-platform-foundation/).
- **Phase 002 - Policy ingestion and hybrid RAG:** six synthetic policies, section-aware ingestion, PostgreSQL full-text search, pgvector retrieval, deterministic eligibility filters, Reciprocal Rank Fusion (RRF), Cohere/BGE adapters, and authoritative citation lookup. Archived under [`2026-09-13-002-policy-ingestion-and-hybrid-rag`](openspec/changes/archive/2026-09-13-002-policy-ingestion-and-hybrid-rag/).
- **Phase 003 - Policy Q&A:** strict question/answer contracts, a Policy Q&A service, minimal LangGraph workflow, governed Model Gateway, OpenAI structured output, deterministic citation validation, safe abstention, structured stage logging, a React question-and-citation experience, and credential-free automated tests. All 27 implementation tasks are complete. The main [`policy-qa` spec](openspec/specs/policy-qa/spec.md) is synced, and the change is archived under [`2026-09-17-003-policy-qa`](openspec/changes/archive/2026-09-17-003-policy-qa/).
- **Phase 004 - Expense compliance assessment:** structured expense intake, clarification and idempotency, separate expense and assessment records, evidence-grounded rule extraction, deterministic Decimal decisions, and a React expense view. The main [`expense-compliance` spec](openspec/specs/expense-compliance/spec.md) is synced and the [`004-expense-compliance-assessment` change](openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/tasks.md) is archived with 19/19 tasks checked. Local automated verification passed; live model generation and browser visual behavior require optional manual checks.

Phase 004 stops at `NEEDS_REVIEW` with a next action. Exception justification, reviewer actions, human interrupt/resume, and autonomous approvals are outside this phase.

## Phase 003 request flow

```text
React Policy Q&A page
  -> POST /api/v1/policy/query
  -> FastAPI/Pydantic validation
  -> PolicyService
  -> LangGraph policy_qa workflow
  -> deterministic ACTIVE/effective/category/region filters
  -> PostgreSQL FTS top 20 + pgvector top 20
  -> RRF fusion with k=60
  -> configured reranker or explicit RRF fallback
  -> top 3-5 evidence chunks
  -> Model Gateway / OpenAI structured output
  -> deterministic citation and source validation
  -> GROUNDED response or INSUFFICIENT_INFORMATION
```

The model receives only selected policy evidence. It returns citation chunk IDs rather than excerpts. The server rechecks those IDs against the reranked set and authoritative stored records, then constructs citation excerpts from stored chunk content. A material answer with no valid citation is discarded and replaced by a safe abstention.

## Prerequisites

- Docker Desktop with the Docker engine running
- Python 3.12 and [uv](https://docs.astral.sh/uv/) for host-run backend development
- Node.js 20 and npm for host-run frontend development
- PowerShell for the commands below
- An OpenAI API key only when manually exercising real answer generation; automated tests do not require OpenAI or Cohere credentials

Run commands from the **project root** unless a step explicitly changes directories.

## Environment setup

Create a local environment file if one does not already exist:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Review these settings in `.env`:

- `POSTGRES_PASSWORD` must match the password embedded in `DATABASE_URL`.
- Host-run processes connect to PostgreSQL on `localhost:5433`. Containers connect internally to `postgres:5432`.
- `OPENAI_API_KEY` is required for a real call to `POST /api/v1/policy/query`.
- `RERANK_PROVIDER=cohere` uses Cohere when `COHERE_API_KEY` is available. With the default `RERANK_FALLBACK_TO_RRF=true`, an unavailable reranker falls back to fused RRF order.
- Set `RERANK_PROVIDER=bge` to exercise the local BGE cross-encoder. Its first run may download the configured model.
- Set `RERANK_PROVIDER=rrf` for a fast retrieval/citation smoke without a model reranker. This validates fallback ordering, not reranker quality.
- Never commit `.env`, API keys, or production credentials.

## Consolidated local validation

The steps below validate infrastructure, migrations, corpus ingestion, the backend, the API, the frontend, and OpenSpec in one sequence.

### 1. Start PostgreSQL and Redis

```powershell
docker compose up -d postgres redis
docker compose ps
docker compose exec -T postgres pg_isready -U policyflow -d policyflow
docker compose exec -T redis redis-cli ping
```

Expected results:

- `policyflow-postgres` and `policyflow-redis` become healthy.
- PostgreSQL reports that it is accepting connections.
- Redis returns `PONG`.

If you changed `POSTGRES_USER` or `POSTGRES_DB`, use those values in the database commands throughout this README.

### 2. Apply and verify the database migration

```powershell
Push-Location backend
uv run --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
uv run --python 3.12 --with-requirements requirements.txt python -m alembic current
Pop-Location
```

Phase 003 adds no migration. The expected head remains:

```text
20260913_0002 (head)
```

Verify pgvector, the RAG tables, and the retrieval indexes:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT extname FROM pg_extension WHERE extname = 'vector'"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema = 'rag' ORDER BY table_name"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT indexname FROM pg_indexes WHERE schemaname = 'rag' ORDER BY indexname"
```

Expect:

- Extension `vector`.
- Tables `policy_document` and `policy_chunk`.
- Indexes including `ix_policy_chunk_fts`, `ix_policy_chunk_vector`, `ix_policy_chunk_metadata`, and `ix_policy_document_status_domain`.

### 3. Ingest the synthetic policy corpus

```powershell
uv run --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
uv run --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
```

The first run on a new database reports `indexed` for `POL-001` through `POL-006`. The second reports `unchanged`, proving content-hash idempotency. The current corpus contains six documents and 50 chunks:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_document"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk"
```

Expected values are `6` and `50`.

Confirm that both PostgreSQL retrieval paths contain usable data:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk WHERE search_vector @@ websearch_to_tsquery('english', 'hotel')"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT id FROM rag.policy_chunk ORDER BY embedding <=> (SELECT embedding FROM rag.policy_chunk LIMIT 1) LIMIT 3"
```

The lexical count should be positive, and the vector query should return three chunk IDs.

### 4. Run targeted Phase 003 backend tests

These tests use injected fake providers and require no OpenAI or Cohere credentials:

```powershell
uv run --python 3.12 --with-requirements backend/requirements.txt pytest `
  backend/tests/test_policy_qa.py `
  backend/tests/test_policy_api_adapters.py `
  backend/tests/test_policy_rag.py -v
```

The latest validated result is:

```text
26 passed
```

Coverage includes request validation, metadata filters, split lexical/vector retrieval, RRF ranks and deduplication, reranker fallback, grounded prompts, Model Gateway retries and schema validation, mocked OpenAI structured output, graph node order, service behavior, API `200`/`422`/`503` contracts, safe abstention, sanitized logs, and the golden dataset.

### 5. Run the complete backend suite with live PostgreSQL

Keep PostgreSQL and Redis running, the migration applied, the corpus ingested, and the project-root `.env` present:

```powershell
uv run --python 3.12 --with-requirements backend/requirements.txt pytest tests backend/tests -v
```

The latest validated result is:

```text
38 passed
```

The live integration tests verify:

- Readiness against PostgreSQL and Redis.
- Alembic head `20260913_0002`.
- pgvector and the required indexes.
- Actual PostgreSQL full-text and vector retrieval.
- Active/effective-date filtering.
- The domestic hotel query retrieves `POL-002` and excludes the international hotel section.
- Final citations resolve to authoritative stored evidence.

If `.env` is absent, the dedicated live policy integration module skips rather than using the dummy unit-test database URL.

### 6. Start the backend locally

In a dedicated PowerShell terminal:

```powershell
cd backend
uv run --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Validate liveness, dependency readiness, and the generated OpenAPI document from another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
$openapi = Invoke-RestMethod http://localhost:8000/openapi.json
$openapi.paths.'/api/v1/policy/query'.post.operationId
```

Expected results:

- `/health` returns `status: ok`.
- `/ready` returns `status: ready`, with PostgreSQL and Redis both `ready`.
- OpenAPI contains exactly one `POST /api/v1/policy/query` operation.
- [Swagger UI](http://localhost:8000/docs) shows health, readiness, admin ingestion, and Policy Q&A endpoints.

### 7. Exercise the Policy Q&A API

A real answer-generation request requires `OPENAI_API_KEY` in the project-root `.env`. Restart the backend after changing environment configuration.

```powershell
$body = @{
  question = "What is the maximum hotel reimbursement allowed for domestic travel?"
  category = "HOTEL"
  region = "INDIA"
} | ConvertTo-Json

$answer = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/policy/query `
  -Headers @{ "X-Request-ID" = "local-policy-qa-001" } `
  -ContentType "application/json" `
  -Body $body

$answer | ConvertTo-Json -Depth 6
```

With the synthetic corpus and successful provider call, expect:

- `request_id` equal to `local-policy-qa-001`.
- `evidence_status` equal to `GROUNDED`.
- An answer supported by the retrieved domestic hotel section.
- At least one verified citation with `policy_code: POL-002`, version, section identity, and a server-created excerpt.
- INR 7,000 appears only when retrieved evidence supports that threshold.

The controlled abstention shape is:

```json
{
  "answer": "I could not find enough verified policy evidence to answer this question reliably.",
  "citations": [],
  "evidence_status": "INSUFFICIENT_INFORMATION"
}
```

Additional API checks:

```powershell
# Question shorter than three characters -> HTTP 422
try {
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query `
    -ContentType "application/json" -Body (@{ question = "x" } | ConvertTo-Json)
} catch { $_.Exception.Response.StatusCode.value__ }

# Unsupported request field -> HTTP 422
try {
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query `
    -ContentType "application/json" `
    -Body (@{ question = "What is the hotel limit?"; unsupported = $true } | ConvertTo-Json)
} catch { $_.Exception.Response.StatusCode.value__ }
```

If `OPENAI_API_KEY` is absent or the configured provider remains unavailable after bounded retry, the endpoint returns HTTP `503`; it does not fabricate an answer. Credential-free grounded and abstention API behavior is covered by the automated tests.

### 8. Build and start the frontend

The frontend currently has no separate test runner. Its verification gate is TypeScript compilation plus the Vite production build:

```powershell
Push-Location frontend
npm ci
npm.cmd run build
Pop-Location
```

Expected result:

```text
tsc -b && vite build
build completed successfully
```

Start the development UI in another terminal:

```powershell
cd frontend
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm.cmd run dev -- --host localhost
```

Open [http://localhost:5173](http://localhost:5173). Vite does not automatically load the project-root `.env`; set `VITE_API_BASE_URL` in the process environment as above or in `frontend/.env.local`. Keep backend `CORS_ORIGINS` aligned with the exact frontend origin.

### 9. Validate the React UI manually

With the backend, PostgreSQL, and Redis running:

1. Confirm the Backend, PostgreSQL, and Redis status cards show **Available**.
2. Confirm the default question is `What is the maximum hotel reimbursement allowed for domestic travel?`.
3. Confirm Category is `HOTEL` and Region is `INDIA`.
4. Submit the question with a configured OpenAI key.
5. Confirm the result shows `GROUNDED`, a policy answer, and verified citation details for `POL-002`.
6. Confirm each citation displays policy code, version, section title, and excerpt.
7. Ask a question for which the corpus has no verified support and confirm the page presents the insufficient-information state without a fabricated threshold.
8. Enter a question shorter than three characters and confirm submission is disabled with validation feedback.
9. Inspect a narrow viewport: the category and region fields should collapse to one column with no horizontal overflow.

Without `OPENAI_API_KEY`, submitting a valid question should display the controlled temporary-unavailable error from the API rather than a policy answer.

### 10. Validate OpenSpec

```powershell
npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
```

Expected results:

- Canonical specs report `3 passed, 0 failed`, including `policy-qa`.
- All strict validation reports `3 passed, 0 failed` with no active changes.
- The active-change list is empty; the archived Phase 003 tasks remain `27/27` complete.

## Docker-only application startup

To run all four services in containers, set `OPENAI_API_KEY` in `.env` when real Policy Q&A generation is required, then run:

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Open:

- Frontend: [http://localhost:5173](http://localhost:5173)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

The backend container applies `alembic upgrade head` before starting FastAPI. After changing any backend environment value, recreate the backend container:

```powershell
docker compose up -d --build --force-recreate backend
```

Stop the application while retaining the PostgreSQL volume:

```powershell
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local database volume and all ingested data.

## Troubleshooting

- **Compose says `POSTGRES_PASSWORD` is missing:** create `.env` from `.env.example`. Keep `POSTGRES_PASSWORD` consistent with `DATABASE_URL`.
- **PostgreSQL rejects the configured password after `.env` changed:** an existing Docker volume retains the credentials used when it was first created. Restore the original local password or intentionally recreate the volume.
- **Host Alembic cannot connect:** the Compose database is exposed at host port `5433`, not `5432`. Containers still use `postgres:5432`.
- **`/ready` returns HTTP 503:** inspect `docker compose ps`, `docker compose logs postgres`, and `docker compose logs redis`. `/health` verifies only that FastAPI is alive.
- **Policy query returns HTTP 503 immediately:** confirm `OPENAI_API_KEY` is present in the environment seen by the backend and restart/recreate the process. Check provider connectivity and configured timeout/retry values.
- **Reranker is unavailable:** provide the configured Cohere key, select `RERANK_PROVIDER=bge`, or keep `RERANK_FALLBACK_TO_RRF=true` for explicit safe fallback.
- **The first embedding or BGE run is slow:** FastEmbed may download the configured model on first use. Automated Phase 003 tests inject fakes and do not require those downloads.
- **Frontend reports that the API is unreachable:** ensure `VITE_API_BASE_URL` points to `http://localhost:8000` and `CORS_ORIGINS` contains the exact browser origin, normally `http://localhost:5173`.
- **The root virtual environment is missing packages:** use the documented `uv run --python 3.12 --with-requirements ...` commands instead of relying on a stale `.venv`.
- **Live integration tests stall or fail to connect:** start PostgreSQL and Redis first, confirm `.env` uses port `5433`, apply the migration, and ingest the corpus before rerunning.

## Safety and data boundaries

- The files under [`policies/synthetic`](policies/synthetic/) are synthetic test policies, not authoritative company rules.
- Policy Q&A does not approve expenses or exceptions.
- LLM output is non-authoritative until deterministic citation validation succeeds.
- Inactive, future-effective, or expired evidence cannot support a grounded answer.
- API keys, database passwords, and other secrets must remain outside source control.
