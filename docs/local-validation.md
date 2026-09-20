# How to execute and validate PolicyFlow AI through Phase 006

This is the consolidated Windows/PowerShell runbook for the platform foundation, synthetic policy ingestion and hybrid retrieval, Policy Q&A, deterministic expense assessment, Phase 005 human-in-the-loop (HITL) exception review, and Phase 006 governed model access.

Run commands from `D:\git-repo\PolicyFlow-AI` unless a step changes directories. Phase 006 is implemented and archived locally; verify the current commit and working tree instead of assuming a publication commit. Automated tests use fake model providers; an OpenAI credential is needed only for optional real browser/API Policy Q&A and complete expense rule extraction.

## 1. Confirm checkout and prerequisites

```powershell
Set-Location D:\git-repo\PolicyFlow-AI
git branch --show-current
git rev-parse --short HEAD
git status --short
docker version
uv --version
node --version
npm.cmd --version
```

Expected baseline: branch `main`, Docker Desktop running, Python 3.12 available through `uv`, and Node.js 20 with npm. Record the displayed commit for traceability. Local documentation or untracked files do not prevent validation; do not use destructive Git cleanup commands to remove unrelated work.

## 2. Prepare environment configuration

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose config --quiet
```

Review these values in `.env` without printing secrets:

```dotenv
POSTGRES_PASSWORD=<local-password>
POSTGRES_PORT=5433
DATABASE_URL=postgresql+psycopg://policyflow:<local-password>@localhost:5433/policyflow
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173
RERANK_PROVIDER=rrf
```

- `POSTGRES_PASSWORD` must match the password in `DATABASE_URL`.
- Host processes use PostgreSQL at `localhost:5433`; Compose services use `postgres:5432`.
- `RERANK_PROVIDER=rrf` is a fast deterministic retrieval smoke, not semantic reranker-quality validation.
- `OPENAI_API_KEY` is optional for automated tests but required for real Policy Q&A and browser-created complete expense assessments.
- Never commit `.env`, credentials, or production data.
- Commands use `uv run --no-project --with-requirements` so a stale virtual environment cannot affect results.

## 3. Start PostgreSQL and Redis

```powershell
docker compose up -d postgres redis
docker compose ps
docker compose exec -T postgres pg_isready -U policyflow -d policyflow
docker compose exec -T redis redis-cli ping
```

Expect both containers to become healthy, PostgreSQL to report `accepting connections`, and Redis to return `PONG`. If `.env` changes `POSTGRES_USER` or `POSTGRES_DB`, substitute those values in database commands.

## 4. Apply and verify migrations through Phase 005

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
Pop-Location
```

Expected head: `20260920_0004 (head)`.

Verify extensions, tables, checkpoint schema, and final-review uniqueness:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT extname FROM pg_extension WHERE extname='vector'"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='app' ORDER BY table_name"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name='checkpoint'"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT indexname FROM pg_indexes WHERE schemaname='app' AND indexname='uq_review_final'"
```

Confirm `vector`, `app.expense`, `app.assessment`, `app.expense_idempotency`, `app.exception_request`, `app.review`, `app.audit_event`, schema `checkpoint`, and index `uq_review_final`. Assessment remains the deterministic Phase 004 result. Human exception status and actions are separate authoritative Phase 005 records; checkpoints are execution state, not business truth.

## 5. Ingest and verify synthetic policies

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_document"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk WHERE search_vector @@ websearch_to_tsquery('english','hotel')"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT id FROM rag.policy_chunk ORDER BY embedding <=> (SELECT embedding FROM rag.policy_chunk LIMIT 1) LIMIT 3"
```

On a fresh database the first ingestion indexes `POL-001` through `POL-006`; the second reports `unchanged`. Expect 6 documents, 50 chunks, a positive hotel full-text count, and three vector-query IDs.

## 6. Run Phase 005 credential-free tests

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q tests/test_exception_hitl.py
Pop-Location
```

These tests cover input bounds, allowed human actions, rejection of autonomous approval, verified summary citations, Decimal variance, LangGraph interrupt/resume, `NEEDS_REVIEW` eligibility, and reviewer-role protection. No model credential is required.

## 7. Run live PostgreSQL HITL integration tests

The corpus must be ingested first because these tests select an authoritative active policy chunk.

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q tests/test_exception_workflow_integration.py
Pop-Location
```

This validates durable exception creation, PostgreSQL checkpoints, same-thread resume after service recreation, APPROVE/REJECT, REQUEST_MORE_INFORMATION, employee continuation, concurrent-decision protection, duplicate-finalization conflict, audit events, safe summary failure, committed-action reconciliation, and the complete API round trip. Tests clean up their synthetic business and checkpoint rows.

## 8. Run the full backend regression suite

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q
Pop-Location
```

Latest verified through-Phase-006 result: `91 passed`. Every collected test must pass.

## 9. Validate the frontend

```powershell
Push-Location frontend
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd audit --omit=dev
Pop-Location
```

Expect 2 frontend tests, successful TypeScript/Vite build, and no known production dependency vulnerabilities. Tests cover employee exception submission and reviewer queue/detail/actions.

## 10. Start and inspect the backend

In a dedicated terminal:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI\backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

From another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
$openapi = Invoke-RestMethod http://localhost:8000/openapi.json
$openapi.paths.PSObject.Properties.Name | Sort-Object
```

Expect healthy/ready responses and the routes below. Swagger is at `http://localhost:8000/docs`.

- `POST /api/v1/expenses/{expense_id}/exceptions`
- `POST /api/v1/exceptions/{exception_id}/information`
- `GET /api/v1/reviews/pending`
- `GET /api/v1/reviews/{exception_id}`
- `POST /api/v1/reviews/{exception_id}/decision`

Demo headers are `X-Demo-Role: EMPLOYEE` for submission/follow-up and `X-Demo-Role: REVIEWER` with optional `X-Demo-User: reviewer-demo` for review APIs.

## 11. Validate clarification and idempotency without a model key

```powershell
$key = [guid]::NewGuid().ToString()
$headers = @{ 'Idempotency-Key'=$key; 'X-Request-ID'='local-clarification-001' }
$body = @{ expense_type='HOTEL'; amount='6500.00'; currency='INR'; location='Bengaluru'; travel_type='DOMESTIC' } | ConvertTo-Json
$first = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $headers -ContentType 'application/json' -Body $body
$replay = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $headers -ContentType 'application/json' -Body $body
$first | ConvertTo-Json -Depth 6
$first.expense_id -eq $replay.expense_id
$first.thread_id -eq $replay.thread_id
```

Expect `INSUFFICIENT_INFORMATION`, `PROVIDE_CLARIFICATION`, missing `purpose` and `receipt_available`, and two `True` comparisons.

```powershell
$partial = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/expenses/$($first.expense_id)/clarifications" -ContentType 'application/json' -Body (@{ purpose='Client meeting' } | ConvertTo-Json)
$partial | ConvertTo-Json -Depth 6
$partial.thread_id -eq $first.thread_id
```

Expect the same expense/thread and only `receipt_available` missing. Completing the request starts model-backed extraction; without a provider, controlled HTTP 503 is correct and no result is fabricated.

## 12. Optionally validate real Q&A and expense assessment

Set `OPENAI_API_KEY` in the root `.env` and restart the backend.

```powershell
$question = @{ question='What is the maximum hotel reimbursement allowed for domestic travel?'; category='HOTEL'; region='INDIA' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query -Headers @{ 'X-Request-ID'='local-policy-qa-001' } -ContentType 'application/json' -Body $question | ConvertTo-Json -Depth 8
```

Expect a grounded answer with verified `POL-002` citation when the provider succeeds; otherwise expect controlled 503.

```powershell
$hotel = @{ expense_type='HOTEL'; amount='9500.00'; currency='INR'; location='Bengaluru'; travel_type='DOMESTIC'; purpose='Client conference'; receipt_available=$true } | ConvertTo-Json
$assessment = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers @{ 'Idempotency-Key'=[guid]::NewGuid().ToString() } -ContentType 'application/json' -Body $hotel
$assessment | ConvertTo-Json -Depth 8
```

With valid POL-002/POL-005 evidence, expect `NEEDS_REVIEW`, limit `7000.00`, next action `SUBMIT_EXCEPTION_JUSTIFICATION`, verified citations, and no autonomous decision.

## 13. Exercise Phase 005 through the API

Submit a valid justification:

```powershell
$exception = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/expenses/$($assessment.expense_id)/exceptions" -Headers @{ 'X-Demo-Role'='EMPLOYEE' } -ContentType 'application/json' -Body (@{ justification='Approved hotels were unavailable near the conference venue.' } | ConvertTo-Json)
$exception | ConvertTo-Json -Depth 8
```

Expect `PENDING_REVIEW`, `WAIT_FOR_REVIEW`, variance `2500.00`, and the same expense/thread.

```powershell
$reviewerHeaders = @{ 'X-Demo-Role'='REVIEWER'; 'X-Demo-User'='reviewer-local' }
$queue = Invoke-RestMethod -Uri http://localhost:8000/api/v1/reviews/pending -Headers $reviewerHeaders
$detail = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)" -Headers $reviewerHeaders
$queue | ConvertTo-Json -Depth 8
$detail | ConvertTo-Json -Depth 10
```

Detail must contain authoritative expense facts, policy identity/version/section, server-derived excerpt, justification, variance, and either a non-authoritative summary or `UNAVAILABLE` summary status.

Verify role protection:

```powershell
try { Invoke-RestMethod -Uri http://localhost:8000/api/v1/reviews/pending -Headers @{ 'X-Demo-Role'='EMPLOYEE' } } catch { $_.Exception.Response.StatusCode.value__ }
```

Expected: `403`.

Exercise more information and final approval:

```powershell
$requested = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)/decision" -Headers $reviewerHeaders -ContentType 'application/json' -Body (@{ decision='REQUEST_MORE_INFORMATION'; comments='Provide manager approval evidence.' } | ConvertTo-Json)
$continued = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/exceptions/$($exception.exception_id)/information" -Headers @{ 'X-Demo-Role'='EMPLOYEE' } -ContentType 'application/json' -Body (@{ information='Synthetic manager approval reference SYNTHETIC-APPROVAL-001.' } | ConvertTo-Json)
$approved = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)/decision" -Headers $reviewerHeaders -ContentType 'application/json' -Body (@{ decision='APPROVE'; comments='Additional information accepted.' } | ConvertTo-Json)
$expenseAfterReview = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/expenses/$($assessment.expense_id)"
$requested, $continued, $approved, $expenseAfterReview | ConvertTo-Json -Depth 8
```

Expect `MORE_INFORMATION_REQUIRED`, then the same exception returning to `PENDING_REVIEW`, then `APPROVED`. The expense response must retain original assessment `NEEDS_REVIEW` and expose the human outcome separately. A second final decision must return 409. Use a separate expense for a manual REJECT path.

## 14. Start and validate the UI

```powershell
Set-Location D:\git-repo\PolicyFlow-AI\frontend
$env:VITE_API_BASE_URL='http://localhost:8000'
npm.cmd run dev -- --host localhost
```

Open `http://localhost:5173` and confirm:

1. Backend, PostgreSQL, and Redis show **Available**.
2. Incomplete expense clarification preserves expense/thread IDs.
3. INR 9500 HOTEL against INR 7000 shows `NEEDS_REVIEW`, never approval.
4. Justification under 20 characters cannot be submitted.
5. Valid submission shows `PENDING REVIEW` and INR 2500 variance.
6. Reviewer queue and detail expose verified evidence and justification.
7. AI content is labeled non-authoritative or safely unavailable.
8. Only APPROVE, REJECT, and REQUEST_MORE_INFORMATION are offered.
9. Duplicate submission is disabled while an action is pending.
10. More-information follow-up returns the same case to the reviewer.
11. Final state and reviewer comments display correctly.
12. A narrow viewport has no horizontal clipping.

## 15. Inspect authoritative records and audit trail

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT id, expense_id, assessment_id, status, variance_amount, thread_id, resume_status, created_at FROM app.exception_request ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT id, exception_id, reviewer_id, decision, comments, reviewed_at FROM app.review ORDER BY reviewed_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT event_type, expense_id, exception_id, review_id, actor_id, previous_state, new_state, created_at FROM app.audit_event ORDER BY created_at DESC LIMIT 25;"
```

Human actions must exist in business tables, reviewer identity must be present, and audit events must reconstruct the transition independently of checkpoint tables.

## 16. Validate OpenSpec and archive state

```powershell
npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
Test-Path openspec/changes/archive/2026-09-20-005-exception-hitl/tasks.md
(Select-String -Path openspec/changes/archive/2026-09-20-005-exception-hitl/tasks.md -Pattern '^- \[x\]').Count
rg -n -- "- \[ \]" openspec/changes/archive/2026-09-20-005-exception-hitl/tasks.md
Test-Path openspec/specs/model-governance/spec.md
Test-Path openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md
(Select-String -Path openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md -Pattern '^- \[x\]').Count
rg -n -- "- \[ \]" openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md
```

Expect six specs passed, zero failed, no active changes, both archives present, Phase 005 with 32 completed tasks, Phase 006 with 42 completed tasks, and no unchecked-task output.

## 17. Optional Docker-only startup

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Open frontend `http://localhost:5173`, Swagger `http://localhost:8000/docs`, and OpenAPI `http://localhost:8000/openapi.json`. After environment changes, recreate the backend with `docker compose up -d --build --force-recreate backend`.

## 18. Stop without deleting local data

Stop host Uvicorn/Vite with `Ctrl+C`, then run:

```powershell
docker compose down
```

Do not run `docker compose down -v` unless you intentionally want to delete the database volume, corpus, and local validation records.

## Troubleshooting

- Docker pipe/API error: start Docker Desktop fully and reopen PowerShell if needed.
- Missing PostgreSQL password: create/review `.env` and align it with `DATABASE_URL`.
- Password fails after `.env` changed: the existing volume retains its original credential; restore it or intentionally recreate only the local volume.
- Host database connection fails: use `localhost:5433`, not `5432`.
- Wrong migration head: run upgrade from `backend`; expected head is `20260920_0004`.
- Live HITL test cannot find a policy chunk: ingest the synthetic corpus first.
- `/ready` is 503: inspect `docker compose ps`, `docker compose logs postgres`, and `docker compose logs redis`.
- Frontend cannot reach API: set `VITE_API_BASE_URL=http://localhost:8000` and align `CORS_ORIGINS`.
- Model endpoint is 503: confirm the key is visible to the backend and restart it; never fabricate a result.
- AI summary is unavailable: this is safe; deterministic facts and human review must remain usable.
- Broken virtual environment: continue using the documented `uv run --no-project` commands.
- Windows async psycopg/checkpoint error: retain the implemented worker-thread `SelectorEventLoop` compatibility path.
- Duplicate final decision returns 409: expected after the first authoritative final action.
- OpenSpec package resolution stalls: rerun with network access and keep version `1.10.0` pinned.

## Phase 005 acceptance summary

At the Phase 005 archive point, validation was complete when infrastructure was healthy; migration head was `20260920_0004`; the six-policy corpus and both retrieval paths worked; targeted, live, and full backend tests passed; frontend tests/build passed; only `NEEDS_REVIEW` entered HITL; variance was deterministic; AI assistance remained grounded and non-authoritative; LangGraph resumed the same thread; all three human actions worked; concurrency could not overwrite the first final decision; audit/business tables remained authoritative; the assessment was not rewritten; and OpenSpec reported five valid specs and 32/32 archived tasks. The current through-Phase-006 OpenSpec baseline is six valid specs and no active changes.

Phase 005 does not include autonomous approval, settlement, SSO, notifications, OCR, fraud detection, multi-agent orchestration, Phase 006 gateway hardening, Phase 007 evaluation expansion, or Phase 008 deployment.

## Phase 006 governed Model Gateway validation

Phase 006 centralizes all three model tasks behind one provider-neutral gateway:

```text
caller -> task route + versioned prompt -> input/evidence guards -> request/thread budget
       -> provider timeout + technical retry -> schema repair (at most once)
       -> output authority/citation guard -> typed result -> downstream deterministic validator
```

No model determines expense compliance or exception approval. Policy Q&A citations still pass the database-backed ACTIVE/effective/source validator, expense rules still pass exact source and Decimal decision logic, and exception review remains human-authoritative.

### 1. Confirm the Phase 006 checkout and archive

```powershell
Set-Location D:\git-repo\PolicyFlow-AI
git branch --show-current
git rev-parse --short HEAD
git status --short
docker version
uv --version
node --version
npm.cmd --version
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
Test-Path openspec/specs/model-governance/spec.md
Test-Path openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md
```

Docker Desktop must respond, Python 3.12 must be available through `uv`, and Node.js/npm must be installed. OpenSpec should report `"changes": []`; both `Test-Path` commands should return `True`. Local uncommitted documentation or architecture exports may appear in `git status`; do not use destructive cleanup commands to remove unrelated work.

### 2. Start infrastructure and verify the database

Phase 006 adds no database migration, but the complete regression suite and application flows require the Phase 005 PostgreSQL schema, synthetic corpus, and Redis.

```powershell
docker compose up -d postgres redis
docker compose ps
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
Pop-Location
```

PostgreSQL and Redis must be healthy. The expected migration head remains `20260920_0004`. Host processes connect to PostgreSQL on `localhost:5433`; containers use `postgres:5432`.

### 3. Configure the gateway safely

Keep secrets only in the root `.env`. Do not print it or commit it. `OPENAI_API_KEY` is optional for all automated tests and required only for real provider calls. The principal Phase 006 controls are:

```text
OPENAI_PRIMARY_MODEL=gpt-4.1-mini
OPENAI_FALLBACK_MODEL=
POLICY_QA_MODEL=
EXPENSE_RULE_MODEL=
EXCEPTION_SUMMARY_MODEL=
MODEL_TIMEOUT_SECONDS=30
MODEL_MAX_RETRIES=2
MODEL_RETRY_BASE_DELAY_MS=250
MODEL_VALIDATION_RETRIES=1
POLICY_QA_MAX_INPUT_TOKENS=8000
POLICY_QA_MAX_OUTPUT_TOKENS=1000
EXPENSE_RULE_MAX_INPUT_TOKENS=8000
EXPENSE_RULE_MAX_OUTPUT_TOKENS=1200
EXCEPTION_SUMMARY_MAX_INPUT_TOKENS=5000
EXCEPTION_SUMMARY_MAX_OUTPUT_TOKENS=600
THREAD_TOKEN_BUDGET=12000
THREAD_BUDGET_TTL_SECONDS=3600
MODEL_CONTEXT_MAX_CHUNKS=5
MODEL_CONTEXT_MAX_CHARS=24000
```

An empty fallback disables fallback. Fallback is technical only: it may follow exhausted timeout, connection, 429, or provider 5xx failures, but never bypasses budgets, evidence checks, schema validation, citation checks, or authority controls. Redis thread accounting fails safely without mutating business state; per-request limits still apply.

Validate configuration names without printing secret values:

```powershell
Test-Path .env
docker compose config --quiet
$inspectedNames = @('DATABASE_URL', 'REDIS_URL', 'MODEL_TIMEOUT_SECONDS',
  'MODEL_MAX_RETRIES', 'THREAD_TOKEN_BUDGET')
$configuredNames = Get-Content .env | Where-Object { $_ -match '^[A-Z][A-Z0-9_]*=' } |
  ForEach-Object { ($_ -split '=', 2)[0] }
$inspectedNames | ForEach-Object { "${_}: $($configuredNames -contains $_)" }
```

`DATABASE_URL` and `REDIS_URL` must be present. A `False` result for a model-control name means the documented application default is in effect. Do not display `OPENAI_API_KEY`, print `.env` into shared logs, or commit `.env`. Automated tests use fake providers and require no OpenAI or Cohere credentials.

### 4. Run focused Phase 006 checks

From `D:\git-repo\PolicyFlow-AI`:

```powershell
docker compose up -d postgres redis
docker compose ps
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_model_gateway_guardrails.py
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_policy_qa.py backend/tests/test_expense_rule_extraction.py backend/tests/test_exception_hitl.py backend/tests/test_policy_api_adapters.py
```

The gateway suite covers strict contracts, routing, prompt registration, configuration overrides, task/scenario matching, prompt-injection detection, request/evidence limits, citation subsets, schema repair, technical fallback, Redis degradation, sanitized telemetry, and adapter error mapping. Expect `10 passed`. The Phase 003–005 focused regression command should report `35 passed`, producing the recorded total of `45 passed`.

### 5. Run complete backend and frontend regressions

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests
Push-Location frontend
npm.cmd test -- --run
npm.cmd run build
Pop-Location
```

The recorded Phase 006 evidence is `91 passed` for the complete backend suite, `2 passed` for frontend tests, and a successful Vite production build. Pending LangGraph serializer-default and Starlette test-client deprecation warnings do not change the result.

### 6. Audit provider isolation, scope, and secrets

```powershell
rg -n "from openai|import openai|AsyncOpenAI" backend/app
rg -n --hidden -g "!.git/**" -g "!.env" -g "!frontend/node_modules/**" -g "!docs/architecture/**" "sk-(proj-)?[A-Za-z0-9_-]{20,}|COHERE_API_KEY=[A-Za-z0-9]{20,}" .
git diff --check
git diff --name-only --cached
git status --short
```

The SDK audit must show lazy SDK import/client construction only in `backend/app/gateway/providers/openai_provider.py`. `gateway/factory.py` may reference the project-owned adapter but must not construct an SDK client. The credential scan and staged-name command should expose no secret or `.env` content. `git diff --check` may print Windows LF/CRLF notices, but must report no whitespace errors. Review `git status` manually because unrelated local files may already exist.

### 7. Start the backend and validate no-key behavior

Ensure `OPENAI_API_KEY` is absent or blank, then start the backend:

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
$headers = @{ 'X-Request-ID' = 'phase-006-no-key' }
$body = @{ question = 'What is the domestic hotel limit?' } | ConvertTo-Json
try {
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query `
    -Headers $headers -ContentType 'application/json' -Body $body
} catch {
  $_.ErrorDetails.Message
}
```

Expect HTTP `503`, code `MODEL_TEMPORARILY_UNAVAILABLE`, a sanitized message, request ID `phase-006-no-key`, and `retryable: true`. No fabricated answer or citation may be returned. Swagger remains available at `http://localhost:8000/docs`, and OpenAPI at `http://localhost:8000/openapi.json`. Stop Uvicorn with `Ctrl+C` before changing model configuration.

### 8. Optionally validate real Policy Q&A

Set `OPENAI_API_KEY` privately in `.env`, optionally set `OPENAI_PRIMARY_MODEL`, and restart Uvicorn. Leave `OPENAI_FALLBACK_MODEL` empty unless a separately available fallback has intentionally been configured.

```powershell
$headers = @{ 'X-Request-ID' = 'phase-006-live-qa' }
$body = @{
  question = 'What is the domestic hotel limit per night?'
  category = 'HOTEL'
  region = 'INDIA'
} | ConvertTo-Json
$answer = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query `
  -Headers $headers -ContentType 'application/json' -Body $body
$answer | ConvertTo-Json -Depth 8
```

Expect either a grounded answer with at least one verified citation and `evidence_status: GROUNDED`, or the exact safe abstention with `INSUFFICIENT_INFORMATION`. A provider-generated policy claim without a verified citation is a failure.

### 9. Optionally validate expense-rule governance

```powershell
$expenseHeaders = @{
  'X-Request-ID' = 'phase-006-expense-9500'
  'Idempotency-Key' = 'phase-006-expense-9500-v1'
}
$expenseBody = @{
  expense_type = 'HOTEL'
  amount = 9500
  currency = 'INR'
  location = 'Bengaluru'
  travel_type = 'DOMESTIC'
  purpose = 'Client workshop'
  receipt_available = $true
} | ConvertTo-Json
$assessment = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses `
  -Headers $expenseHeaders -ContentType 'application/json' -Body $expenseBody
$assessment | ConvertTo-Json -Depth 10
```

With the synthetic INR 7000 hotel rule, expect `NEEDS_REVIEW` and `policy_limit: 7000`. The model extracts evidence-backed rules; deterministic Decimal code selects the outcome. Repeat the same request and idempotency key to confirm the expense identity is reused rather than duplicated. A complete INR 6500 case should remain `COMPLIANT` when the same verified limit applies.

### 10. Inspect telemetry and authority boundaries

During live calls, gateway telemetry may contain task, provider/model, prompt version, request/thread IDs, available token counts, latency, transport retries, validation repairs, fallback flag, guardrail outcome, and sanitized error category. It must not contain API keys, authorization headers, database credentials, complete prompts, full policy documents, employee justification, or raw provider payloads/exceptions.

Confirm these boundaries:

- `POLICY_QA` answers policy questions but does not decide expense compliance.
- `EXPENSE_POLICY_RULE` extracts structured rules but does not authoritatively choose `COMPLIANT`, `NON_COMPLIANT`, or `NEEDS_REVIEW`.
- `EXCEPTION_REVIEW_SUMMARY` summarizes facts but cannot approve, reject, or recommend a final outcome.
- Returned citation IDs are a subset of server-supplied evidence.
- Database-backed ACTIVE/effective/source and exact-amount validators remain authoritative after gateway generation.

### 11. Validate the archived OpenSpec state

```powershell
npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
Test-Path openspec/specs/model-governance/spec.md
Test-Path openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md
(Select-String -Path openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md -Pattern '^- \[x\]').Count
rg -n -- "- \[ \]" openspec/changes/archive/2026-09-20-006-model-gateway-guardrails/tasks.md
```

Expect six canonical specs passed, zero failures, no active changes, both paths present, `42` completed tasks, and no unchecked-task output. The canonical model-governance spec contains 12 requirements. Do not run change-specific validation after archive because the active change no longer exists.

### 12. Controlled-failure expectations

- No key or unavailable provider produces a controlled unavailable response; it does not fabricate policy output.
- Oversized input or evidence fails before provider invocation; authoritative evidence is never silently truncated.
- A transient transport failure retries only within the configured bound.
- Invalid structured output receives at most one explicit schema-repair request.
- An unknown citation, final expense decision, or exception approval/rejection language is rejected.
- Exception summary failure leaves deterministic facts and human reviewer authority available.

The credential-free focused suite is the repeatable evidence for timeout, 429, invalid schema, repair, fallback, injection, oversized context, Redis failure, and telemetry sanitization. Do not deliberately exhaust a paid quota or expose a key to reproduce those cases manually.

### 13. Acceptance checklist

Phase 006 validation is complete when:

1. PostgreSQL and Redis are healthy, and migration head is `20260920_0004`.
2. Focused gateway tests report 10 passed and earlier-phase focused regressions report 35 passed.
3. The complete backend suite reports 91 passed without live credentials.
4. Frontend tests report 2 passed and the production build succeeds.
5. SDK construction exists only in the OpenAI adapter.
6. No secret, `.env`, or raw provider payload enters the change scope.
7. Missing credentials yield a controlled `503`, never fabricated output.
8. Optional live output is typed, evidence-grounded, and citation-validated.
9. INR 9500 versus INR 7000 remains deterministically `NEEDS_REVIEW`.
10. Exception finalization remains restricted to an authorized reviewer.
11. Telemetry is sanitized while retaining correlation, retry, and token metadata.
12. OpenSpec reports six valid specs, 42/42 archived tasks, and no active changes.

### Phase 006 troubleshooting

- Import failure: use the exact `uv run --no-project --python 3.12 --with-requirements backend/requirements.txt` command from the repository root.
- Key configured but API remains `503`: restart/recreate the backend so it reloads `.env`; verify connectivity without printing the key.
- Expense API is unavailable: verify PostgreSQL, Redis, migrations, corpus ingestion, and configured reranker/provider.
- Thread budget is unexpectedly exhausted: wait for the TTL or clear only the intended local Redis database; the counter is not business state.
- Oversized input is rejected: expected; authoritative evidence is not silently truncated. Reduce optional context or use a deliberately reviewed limit.
- Schema repair fails: expected after one repair attempt; the gateway safely rejects the result.
- Fallback does not run: it must be configured and follows only classified technical failures, never evidence, citation, guardrail, or business-rule rejection.
- Secret scan floods output: retain the documented generated-asset exclusions and inspect application/configuration source separately.
- OpenSpec cannot find the Phase 006 change: expected after archive; validate `--specs` and `--all`, then inspect the dated archive path.
- Port 8000 is occupied: stop the existing process or use another port and adjust every validation URL consistently.

Phase 006 stops here. Observability exporters, evaluation datasets/scoring, dashboards/alerts, and deployment expansion are deferred to Phase 007 or later.

## Phase 007 local validation: observability and evaluation

Run this section from D:\git-repo\PolicyFlow-AI.

### 1. Infrastructure and corpus

    docker compose ps
    docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT version_num FROM alembic_version;"
    docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT COUNT(*) FROM rag.policy_document WHERE status='ACTIVE';"
    docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT COUNT(*) FROM rag.policy_chunk;"

Expect PostgreSQL and Redis healthy, migration 20260920_0004, six ACTIVE policy
documents (POL-001 through POL-006), and 50 chunks. If the corpus is absent, run
the Phase 002 ingestion procedure before retrieval evaluation.

### 2. Dependencies and import boundaries

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -c "import langsmith, ragas, deepeval; print('Phase 007 imports OK')"
    rg -n "import ragas|from ragas|import deepeval|from deepeval" backend/app

The dependency families are bounded to LangSmith 0.13.x, Ragas 0.3.x, and
DeepEval 3.x. The runtime-source audit must return no evaluator imports.

### 3. Disabled and mocked tracing

Keep LANGSMITH_TRACING=false, LANGSMITH_API_KEY blank, and
ENABLE_AI_EVALUATION=false, then run:

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_observability.py

The suite requires no network and covers immutable correlation, recursive
redaction, size bounds, normalized errors, disabled and mocked exporters,
exporter outage, parent/child spans, exception passthrough, concurrent requests,
and safe metric builders.

For an optional live trace, set LANGSMITH_TRACING=true, set a private
LANGSMITH_API_KEY, choose LANGSMITH_PROJECT=policyflow-ai-local, restart the
backend, and issue one Policy Q&A request. Verify request/thread correlation
across validation, filters, hybrid retrieval, RRF, reranking, governed generation,
citation validation, and final response. Raw question, prompts, policy text,
credentials, purpose, justification, and reviewer comments must be absent.
Disconnecting LangSmith must not change the API result.

### 4. PostgreSQL-backed deterministic evaluations

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_retrieval --strategy hybrid
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_decisions

Expect retrieval_evaluation.json, citation_evaluation.json, and
expense_decisions.json under evaluation/reports. Precision@5 must be at least
0.80, Recall@10 at least 0.90, citation correctness at least 0.95, and decision
accuracy exactly 1.00. Sub-threshold commands exit non-zero and identify failed
metrics/cases. Retrieval and citations use live PostgreSQL eligibility; expense
outcomes use exact Decimal rules without an LLM judge.

### 5. Three-strategy benchmark

    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.benchmark

Inspect evaluation/reports/retrieval_benchmark.json. Vector-only, hybrid
FTS+vector+RRF, and hybrid+rerank must have identical case IDs and report
Precision@5, Recall@10, MRR, and average latency. The default command uses an
explicit unavailable evaluator reranker and marks that arm fallback; it must not
be claimed as genuine reranked quality. Inject an explicitly authorized local BGE
or Cohere reranker only for a controlled live benchmark.

### 6. External-evaluator skip and baseline behavior

    $env:ENABLE_AI_EVALUATION = "false"
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.ragas.evaluate_rag
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.deepeval.evaluate_agent
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.summarize

Expect Ragas and DeepEval status skip, exit code zero, and SUMMARY.md linking all
reports. A live baseline is operator-invoked only with
ENABLE_AI_EVALUATION=true and a private evaluator key. Phase 007 validates
current-version dataset/test-case conversion but does not invent paid scores or
enforce an unapproved external threshold.

### 7. Full regressions

    $env:PYTHONPATH = "backend;."
    uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests
    Push-Location frontend
    npm.cmd test -- --run
    npm.cmd run build
    Pop-Location

Recorded Phase 007 evidence is 116 backend tests passed, 2 frontend tests passed,
and a successful Vite production build. LangGraph serializer-default and
Starlette test-portal deprecation warnings are non-failing.

### 8. Security, generated-file, and scope audits

    rg -n "user_query|purpose|justification|reviewer_comments|content" backend/app/observability
    rg -n --hidden -g "!.git/**" -g "!.env" -g "!frontend/node_modules/**" -g "!docs/architecture/**" "sk-(proj-)?[A-Za-z0-9_-]{20,}" .
    git diff --check
    git diff --name-only --cached
    git status --short

Forbidden field names may occur only in redaction rules/tests, never as exported
values. The secret scan must return no credential. Do not stage .env, generated
reports, or unrelated user files. Report timestamps and local latency are
environment-specific, so reports remain ignored build artifacts.

### 9. CI and OpenSpec

    npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
    npx.cmd -y @fission-ai/openspec@1.10.0 list --json
    Test-Path openspec/specs/observability-evaluation/spec.md
    Test-Path openspec/changes/archive/2026-09-20-007-observability-evaluation/tasks.md
    (Select-String -Path openspec/changes/archive/2026-09-20-007-observability-evaluation/tasks.md -Pattern '^- \[x\]').Count

The default RAG-evaluation job uses no external evaluator secret, runs
deterministic tests/reports, and uploads artifacts. Live external evaluation is a
separate guarded manual job. Expect seven canonical specs, zero strict failures,
an empty active-change list, both Phase 007 paths to exist, and 56 completed
archived tasks. Change-specific validation is no longer available after archive.

### 10. Authority and deferred scope

Tracing observes but never determines COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW,
APPROVE, or REJECT. PostgreSQL evidence eligibility, deterministic Decimal rules,
citation validation, and authorized human actions remain authoritative. Ragas and
DeepEval never run in FastAPI startup or request execution.

Phase 007 defers AWS/CloudWatch, Prometheus/Grafana, production dashboards and
alerts, durable cost accounting, new retrieval algorithms, and all Phase 008
deployment hardening.
