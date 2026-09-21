# PolicyFlow AI local validation — Phases 001 through 007

This is the consolidated Windows PowerShell runbook for validating the PolicyFlow AI platform from Phase 001 through Phase 007. It covers the platform foundation, policy ingestion and hybrid retrieval, grounded Policy Q&A, deterministic expense assessment, human exception review, the governed Model Gateway, and observability/evaluation.

Run commands from `D:\git-repo\PolicyFlow-AI` unless a step explicitly changes directories. Record the Git commit you validate. The current repository also contains Phase 008 deployment work; that work is outside this guide and is documented in `docs/aws-deployment.md` and `docs/phase-008-implementation-report.md`.

## 1. What each phase validates

| Phase | Capability | Primary evidence |
| --- | --- | --- |
| 001 | FastAPI/React foundation, PostgreSQL, Redis, health/readiness | foundation tests, `/health`, `/ready`, UI status |
| 002 | Synthetic policy ingestion, PostgreSQL FTS, pgvector, hybrid retrieval | idempotent ingestion, corpus SQL, retrieval tests |
| 003 | Evidence-grounded Policy Q&A | strict response contract, citations, safe abstention |
| 004 | Expense intake and deterministic compliance decisions | clarification, idempotency, rules, evidence, persistence |
| 005 | Human-in-the-loop exception review | durable workflow, role checks, resume, audit trail |
| 006 | Governed provider-neutral model access | retries, fallback, budgets, kill switch, secret isolation |
| 007 | Safe tracing and repeatable evaluation | redaction, deterministic metrics, benchmark, reports |

AI output is never the authority for policy eligibility, expense decisions, human approvals, or audit history. PostgreSQL evidence, deterministic rules, validated citations, and authorized reviewer actions remain authoritative.

## 2. Prerequisites and checkout

Required locally:

- Docker Desktop with the Linux container engine running
- Git
- Python 3.12 available through `uv`
- Node.js 20 and npm
- Internet access the first time images, Python packages, npm packages, models, or the pinned OpenSpec CLI are downloaded

Verify the checkout and tools:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI
git branch --show-current
git rev-parse HEAD
git status --short
docker version
docker compose version
uv --version
node --version
npm.cmd --version
```

Expected: the intended branch and commit are displayed, Docker Desktop responds, Python 3.12 can be selected by `uv`, and Node reports major version 20. A dirty worktree does not make a test invalid, but record its changed files so the result is reproducible. Do not discard unrelated work merely to make the tree clean.

## 3. Create the private local environment

The repository intentionally does not publish an environment template. Create `D:\git-repo\PolicyFlow-AI\.env` manually and keep it untracked. Use a private local password in both PostgreSQL settings and `DATABASE_URL`:

```dotenv
APP_ENV=local
POSTGRES_DB=policyflow
POSTGRES_USER=policyflow
POSTGRES_PASSWORD=<private-local-password>
POSTGRES_PORT=5433
DATABASE_URL=postgresql+psycopg://policyflow:<private-local-password>@localhost:5433/policyflow
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000
RERANK_PROVIDER=rrf
LANGSMITH_TRACING=false
ENABLE_AI_EVALUATION=false
```

Important boundaries:

- Host processes use PostgreSQL on `localhost:5433`; containers use `postgres:5432`.
- Host processes use Redis on `localhost:6379`; the backend container uses `redis:6379`.
- `RERANK_PROVIDER=rrf` gives a credential-free deterministic local path. It is not a semantic reranker-quality claim.
- `OPENAI_API_KEY` is optional for automated tests. It is required for a real Policy Q&A generation call and a fully populated expense assessment.
- `COHERE_API_KEY` is optional and only needed when deliberately selecting the Cohere reranker.
- `POLICY_ADMIN_TOKEN` and `LANGSMITH_API_KEY` are optional for their protected/live paths.
- Never print, stage, or commit `.env` or provider credentials.

Confirm Compose can resolve the configuration without displaying secrets:

```powershell
docker compose config --quiet
git check-ignore .env
```

Expected: Compose exits successfully and Git reports `.env` as ignored.

## 4. Start infrastructure and apply migrations

Start only PostgreSQL and Redis while running tests or host processes:

```powershell
docker compose up -d postgres redis
docker compose ps
docker compose exec -T postgres pg_isready -U policyflow -d policyflow
docker compose exec -T redis redis-cli ping
```

Expected: both services become healthy, PostgreSQL reports `accepting connections`, and Redis returns `PONG`.

Apply every migration through the Phase 005 schema head:

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
Pop-Location
```

Expected migration head: `20260920_0004 (head)`.

Verify pgvector and the durable schemas:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT extversion FROM pg_extension WHERE extname='vector';"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT version_num FROM alembic_version;"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT table_schema || '.' || table_name FROM information_schema.tables WHERE table_schema IN ('app','rag') ORDER BY 1;"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name='checkpoint';"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT indexname FROM pg_indexes WHERE schemaname='app' AND indexname='uq_review_final';"
```

Confirm:

- a pgvector version is returned;
- the Alembic version is `20260920_0004`;
- `rag.policy_document` and `rag.policy_chunk` exist;
- the application tables include expense, assessment, idempotency, exception, review, and audit records;
- the `checkpoint` schema exists; and
- `uq_review_final` prevents multiple authoritative final reviews.

## 5. Phase 002 — ingest and verify the synthetic corpus

Run ingestion twice to prove content-hash idempotency:

```powershell
$env:PYTHONPATH = "backend;."
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
```

On a fresh database the first run indexes `POL-001` through `POL-006`. The second run reports the documents as unchanged rather than creating duplicates.

Validate the live PostgreSQL corpus and both retrieval primitives:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_document WHERE status='ACTIVE';"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk;"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk WHERE search_vector @@ websearch_to_tsquery('english','hotel');"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT id FROM rag.policy_chunk ORDER BY embedding <=> (SELECT embedding FROM rag.policy_chunk LIMIT 1) LIMIT 3;"
```

Expected baseline: 6 ACTIVE documents, 50 chunks, a positive full-text result, and three IDs from the vector-distance query. This proves that validation uses PostgreSQL FTS and pgvector rather than a Python-only approximation.

Run the focused Phase 002 tests:

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_policy_rag.py backend/tests/test_policy_rag_integration.py backend/tests/test_policy_api_adapters.py
```

The integration module uses `DATABASE_URL` from the root `.env`. A skipped live module is not equivalent to a PostgreSQL validation pass; fix the environment and rerun it.

## 6. Phase 001 through Phase 007 automated validation

Set the import path once in the PowerShell session:

```powershell
$env:PYTHONPATH = "backend;."
```

### Phase 001 — foundation

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q tests/unit/test_foundation.py tests/unit/test_health.py tests/integration/test_readiness.py
```

This checks repository structure, configuration, health, readiness, and dependency failure behavior.

### Phase 003 — grounded Policy Q&A

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_policy_qa.py
```

This checks input bounds, grounded response contracts, citation validation, safe abstention, and provider-failure handling.

### Phase 004 — deterministic expense compliance

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_expense_schema.py backend/tests/test_expense_rules.py backend/tests/test_expense_evidence.py backend/tests/test_expense_rule_extraction.py backend/tests/test_expense_api.py backend/tests/test_expense_repository_integration.py backend/tests/test_expense_workflow_integration.py
```

This checks strict intake, missing-field clarification, idempotency, source-bound rule extraction, Decimal decisions, persistence, and workflow continuity. Live integration tests must run, not silently skip, when claiming database validation.

### Phase 005 — exception and human review

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_exception_hitl.py backend/tests/test_exception_workflow_integration.py
```

This checks review eligibility, variance, role authorization, LangGraph interrupt/resume, more-information loops, final approval/rejection, concurrency protection, and audit events. No test should permit an LLM to approve or reject an expense.

### Phase 006 — Model Gateway guardrails

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_model_gateway_guardrails.py
```

This checks provider isolation, purpose-specific models, structured output validation, retry/fallback behavior, timeouts, kill-switch behavior, token/thread budgets, and secret-safe telemetry. Automated tests use controlled fake providers and do not require real credentials.

### Phase 007 — observability and evaluation

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q backend/tests/test_observability.py backend/tests/test_evaluation.py
```

This checks immutable correlation fields, recursive redaction, payload bounds, normalized errors, disabled and mocked exporters, exporter outages, trace relationships, concurrent requests, metric builders, evaluator gates, and explicit skip behavior.

### Complete regression

Run the entire current Python suite after all focused checks:

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt pytest -q tests backend/tests
```

The current repository baseline is `135 passed`. Because this command validates the current checkout, it also collects the later Phase 008 infrastructure tests. For Phase 001–007 acceptance, every applicable test must pass and live PostgreSQL modules must not be skipped. Non-failing LangGraph serializer-default or Starlette portal deprecation warnings may be reported separately.

## 7. Frontend tests and production build

```powershell
Push-Location frontend
npm.cmd ci
npm.cmd test -- --run
npm.cmd run build
npm.cmd audit --omit=dev
Pop-Location
```

Expected Phase 001–007 evidence: 2 Vitest tests pass, TypeScript compiles, the Vite production build succeeds, and the production dependency audit reports no known vulnerabilities. The tests cover the employee expense/exception flow and reviewer queue/detail/actions.

## 8. Start the application

Choose one startup mode. Do not run the containerized backend and a host backend on port 8000 at the same time.

### Option A — full Docker Compose stack

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail 100 backend
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Compose applies Alembic migrations before starting the backend. Wait for PostgreSQL, Redis, and backend to be healthy. The URLs are:

- frontend: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`
- health: `http://localhost:8000/health`
- readiness: `http://localhost:8000/ready`

### Option B — infrastructure in Docker, apps on the host

Terminal 1:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI\backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI\frontend
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm.cmd run dev -- --host localhost
```

Terminal 3 is used for the API checks below.

## 9. Phase 001 runtime checks

```powershell
$health = Invoke-RestMethod http://localhost:8000/health
$ready = Invoke-RestMethod http://localhost:8000/ready
$openapi = Invoke-RestMethod http://localhost:8000/openapi.json
$health | ConvertTo-Json -Depth 5
$ready | ConvertTo-Json -Depth 5
$openapi.paths.PSObject.Properties.Name | Sort-Object
```

Expect health and readiness success and the Policy Q&A, expense, exception, and review routes to be present. Stop PostgreSQL or Redis temporarily only if you deliberately want to prove `/ready` reports a dependency failure; restart it before continuing.

## 10. Phase 003 — real Policy Q&A smoke

This smoke needs a valid `OPENAI_API_KEY` visible to the backend. After adding or changing the key, restart/recreate the backend. If no model key is configured, a controlled failure or safe unavailable response is correct; a fabricated answer is not.

```powershell
$question = @{
  question = 'What is the maximum hotel reimbursement allowed for domestic travel?'
  category = 'HOTEL'
  region = 'INDIA'
} | ConvertTo-Json

$answer = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/policy/query `
  -Headers @{ 'X-Request-ID' = 'local-policy-qa-001' } `
  -ContentType 'application/json' `
  -Body $question
$answer | ConvertTo-Json -Depth 10
```

For a successful answer, require `evidence_status=GROUNDED`, at least one verified citation, and policy code/version/section/chunk identity for every citation. If evidence is inadequate, require `INSUFFICIENT_INFORMATION`, the safe abstention text, and no citations.

## 11. Phase 004 — expense clarification and idempotency

The incomplete request below is credential-free because it stops before model-backed rule extraction:

```powershell
$idempotencyKey = [guid]::NewGuid().ToString()
$expenseHeaders = @{
  'Idempotency-Key' = $idempotencyKey
  'X-Request-ID' = 'local-expense-001'
}
$incompleteExpense = @{
  expense_type = 'HOTEL'
  amount = '6500.00'
  currency = 'INR'
  location = 'Bengaluru'
  travel_type = 'DOMESTIC'
} | ConvertTo-Json

$first = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $expenseHeaders -ContentType 'application/json' -Body $incompleteExpense
$replay = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $expenseHeaders -ContentType 'application/json' -Body $incompleteExpense
$first | ConvertTo-Json -Depth 8
$first.expense_id -eq $replay.expense_id
$first.thread_id -eq $replay.thread_id
```

Expect `INSUFFICIENT_INFORMATION`, next action `PROVIDE_CLARIFICATION`, missing `purpose` and `receipt_available`, and both comparisons equal to `True`.

```powershell
$partial = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/expenses/$($first.expense_id)/clarifications" `
  -ContentType 'application/json' `
  -Body (@{ purpose = 'Client meeting' } | ConvertTo-Json)
$partial | ConvertTo-Json -Depth 8
$partial.thread_id -eq $first.thread_id
```

Expect the same expense/thread and only `receipt_available` still missing. Completing the request triggers governed model-backed rule extraction; without a provider key, controlled HTTP 503 is expected and no decision may be invented.

With a valid model credential, create an over-limit expense for the Phase 005 journey:

```powershell
$hotelExpense = @{
  expense_type = 'HOTEL'
  amount = '9500.00'
  currency = 'INR'
  location = 'Bengaluru'
  travel_type = 'DOMESTIC'
  purpose = 'Client conference'
  receipt_available = $true
} | ConvertTo-Json

$assessment = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/v1/expenses `
  -Headers @{ 'Idempotency-Key' = [guid]::NewGuid().ToString(); 'X-Request-ID' = 'local-expense-002' } `
  -ContentType 'application/json' `
  -Body $hotelExpense
$assessment | ConvertTo-Json -Depth 10
```

With verified `POL-002`/`POL-005` evidence, expect `NEEDS_REVIEW`, policy limit `7000.00`, next action `SUBMIT_EXCEPTION_JUSTIFICATION`, confidence/citations, and no autonomous approval.

## 12. Phase 005 — end-to-end human review

This section continues from `$assessment` above. Demo authorization is intentionally explicit:

- employee actions: `X-Demo-Role: EMPLOYEE`
- reviewer actions: `X-Demo-Role: REVIEWER`
- optional reviewer identity: `X-Demo-User`

Submit an exception:

```powershell
$employeeHeaders = @{ 'X-Demo-Role' = 'EMPLOYEE' }
$exception = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/expenses/$($assessment.expense_id)/exceptions" `
  -Headers $employeeHeaders `
  -ContentType 'application/json' `
  -Body (@{ justification = 'Approved hotels were unavailable near the conference venue.' } | ConvertTo-Json)
$exception | ConvertTo-Json -Depth 10
```

Expect `PENDING_REVIEW`, `WAIT_FOR_REVIEW`, variance `2500.00`, and the original expense/thread identity.

Inspect the queue and detail:

```powershell
$reviewerHeaders = @{ 'X-Demo-Role' = 'REVIEWER'; 'X-Demo-User' = 'reviewer-local' }
$queue = Invoke-RestMethod -Uri http://localhost:8000/api/v1/reviews/pending -Headers $reviewerHeaders
$detail = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)" -Headers $reviewerHeaders
$queue | ConvertTo-Json -Depth 10
$detail | ConvertTo-Json -Depth 12
```

The detail must show authoritative expense facts, policy identity/version/section, server-derived excerpts, justification, variance, and either a non-authoritative review summary or `summary_status=UNAVAILABLE`.

Prove reviewer-role enforcement:

```powershell
try {
  Invoke-RestMethod -Uri http://localhost:8000/api/v1/reviews/pending -Headers $employeeHeaders
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected status: `403`.

Exercise request-more-information, employee continuation, and final approval:

```powershell
$requested = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)/decision" `
  -Headers $reviewerHeaders `
  -ContentType 'application/json' `
  -Body (@{ decision = 'REQUEST_MORE_INFORMATION'; comments = 'Provide manager approval evidence.' } | ConvertTo-Json)

$continued = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/exceptions/$($exception.exception_id)/information" `
  -Headers $employeeHeaders `
  -ContentType 'application/json' `
  -Body (@{ information = 'Synthetic manager approval reference SYNTHETIC-APPROVAL-001.' } | ConvertTo-Json)

$approved = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/reviews/$($exception.exception_id)/decision" `
  -Headers $reviewerHeaders `
  -ContentType 'application/json' `
  -Body (@{ decision = 'APPROVE'; comments = 'Additional information accepted.' } | ConvertTo-Json)

$expenseAfterReview = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/expenses/$($assessment.expense_id)"
$requested, $continued, $approved, $expenseAfterReview | ConvertTo-Json -Depth 12
```

Expect `MORE_INFORMATION_REQUIRED`, then the same exception back at `PENDING_REVIEW`, then `APPROVED`. The original deterministic assessment remains `NEEDS_REVIEW`; the human outcome is stored and exposed separately. A second final action must return HTTP 409. Use a separate expense/exception to validate `REJECT` rather than attempting to overwrite the approved result.

## 13. Phase 006 — live guardrail checks

Automated tests provide the deterministic Phase 006 evidence. For a real-provider smoke, keep credentials only in `.env`, restart the backend, issue one Policy Q&A request, and inspect logs without exposing prompt text or secrets:

```powershell
docker compose logs --tail 200 backend
rg -n "OPENAI_API_KEY|COHERE_API_KEY|LANGSMITH_API_KEY" backend/app
```

Validate these outcomes:

- application services call the Model Gateway rather than provider SDKs directly;
- invalid structured output is rejected or retried within configured limits;
- timeout, unavailable provider, exhausted budget, or kill switch produces a controlled failure;
- fallback never bypasses schema validation, evidence validation, or authority boundaries;
- logs/telemetry contain correlation and operational metadata, not keys, raw prompts, policy text, purpose, justification, or reviewer comments.

The source search will legitimately find configuration field names. It must not find hard-coded secret values.

## 14. Phase 007 — deterministic evaluation and tracing

Keep external evaluation and live tracing disabled for the reproducible baseline:

```powershell
$env:LANGSMITH_TRACING = "false"
$env:ENABLE_AI_EVALUATION = "false"
$env:PYTHONPATH = "backend;."
```

Run PostgreSQL-backed retrieval and deterministic decision evaluation:

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_retrieval --strategy hybrid
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.run_decisions
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.benchmark
```

Inspect generated local reports in `evaluation/reports`:

- `retrieval_evaluation.json`
- `citation_evaluation.json`
- `expense_decisions.json`
- `retrieval_benchmark.json`

Required gates:

| Metric | Required | Recorded Phase 007 baseline |
| --- | ---: | ---: |
| Precision@5 | at least 0.80 | 0.9091 |
| Recall@10 | at least 0.90 | 0.9091 |
| MRR | reported | 0.9091 |
| Citation correctness | at least 0.95 | 1.0000 |
| Valid citation coverage | reported | 1.0000 |
| Expense decision accuracy | exactly 1.00 | 1.0000 |

A failed threshold must make the command exit non-zero and identify the failed metric/case. The benchmark compares vector-only, hybrid FTS+vector+RRF, and hybrid+rerank over identical case IDs. If the evaluator reranker is unavailable, the report must label the fallback; do not claim it as genuine reranked quality.

Validate the explicit external-evaluator skip path and generate the summary:

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.ragas.evaluate_rag
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.deepeval.evaluate_agent
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python -m evaluation.summarize
```

Expect Ragas and DeepEval to report `skip` with exit code zero while `ENABLE_AI_EVALUATION=false`, and expect `evaluation/reports/SUMMARY.md` to link the reports. Generated reports are local artifacts; timestamps and latency are environment-specific.

Optional live LangSmith validation uses the host-backend startup in Option B (the current Compose backend does not forward the LangSmith settings):

1. Put a private `LANGSMITH_API_KEY` in `.env`.
2. Set `LANGSMITH_TRACING=true` and `LANGSMITH_PROJECT=policyflow-ai-local`.
3. Restart the backend and issue one Policy Q&A request.
4. Verify request/thread correlation across validation, filters, retrieval, fusion/reranking, governed generation, citation validation, and response.
5. Verify raw questions, prompts, policy text, credentials, expense purpose, exception justification, and reviewer comments are absent.
6. Disable/disconnect LangSmith and prove the API result is unchanged.

Tracing observes execution; it never determines an expense or review outcome. Ragas and DeepEval do not run during FastAPI startup or request execution.

## 15. Browser end-to-end checks

Open `http://localhost:5173` and validate at desktop and narrow/mobile widths:

1. Backend, PostgreSQL, and Redis show available.
2. Policy Q&A shows grounded answers only with citations and clearly shows abstention otherwise.
3. An incomplete expense asks for the missing fields and preserves expense/thread IDs.
4. Replaying the same idempotency key does not create a duplicate expense.
5. INR 9,500 HOTEL against INR 7,000 evidence shows `NEEDS_REVIEW`, never automatic approval.
6. Exception justification shorter than 20 characters is rejected client-side/server-side.
7. A valid exception shows `PENDING REVIEW` and INR 2,500 variance.
8. The reviewer queue/detail shows evidence, justification, and non-authoritative summary status.
9. Reviewer actions are limited to APPROVE, REJECT, and REQUEST_MORE_INFORMATION.
10. A more-information response resumes the same exception/workflow thread.
11. A final human state and reviewer comments display separately from the original assessment.
12. Duplicate final submission is prevented or returns conflict.
13. No sensitive raw text or credential appears in browser console/network metadata beyond the intended API request body.
14. Pages remain usable without horizontal clipping at a narrow viewport.

Browser evidence is a manual gate. Do not mark it complete from unit tests alone.

## 16. Inspect authoritative records and audit history

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT id, expense_type, amount, currency, thread_id, created_at FROM app.expense ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT expense_id, decision, policy_limit, confidence, created_at FROM app.assessment ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT id, expense_id, assessment_id, status, variance_amount, thread_id, resume_status, created_at FROM app.exception_request ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT id, exception_id, reviewer_id, decision, comments, reviewed_at FROM app.review ORDER BY reviewed_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U policyflow -d policyflow -c "SELECT event_type, expense_id, exception_id, review_id, actor_id, metadata_json, created_at FROM app.audit_event ORDER BY created_at DESC LIMIT 25;"
```

Verify human actions exist in business tables, reviewer identity is recorded, and audit events reconstruct the transition independently of checkpoint state. Checkpoints coordinate execution; they are not the source of truth for a financial decision.

## 17. OpenSpec and archive validation

Use the pinned CLI:

```powershell
npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
```

Then verify all Phase 001–007 archives and no unchecked archived task:

```powershell
$phaseArchives = @(
  '2026-09-13-001-platform-foundation',
  '2026-09-13-002-policy-ingestion-and-hybrid-rag',
  '2026-09-17-003-policy-qa',
  '2026-09-18-004-expense-compliance-assessment',
  '2026-09-20-005-exception-hitl',
  '2026-09-20-006-model-gateway-guardrails',
  '2026-09-20-007-observability-evaluation'
)

foreach ($archive in $phaseArchives) {
  $taskFile = "openspec/changes/archive/$archive/tasks.md"
  [pscustomobject]@{
    Archive = $archive
    Exists = Test-Path $taskFile
    Completed = (Select-String -Path $taskFile -Pattern '^- \[x\]').Count
    Pending = (Select-String -Path $taskFile -Pattern '^- \[ \]').Count
  }
}
```

Expected for the Phase 001–007 baseline: all seven archives exist, every archive reports `Pending=0`, and all canonical specs validate strictly. The current checkout can legitimately show the separate `008-aws-deployment-hardening` change as active; do not misreport that as unfinished Phase 001–007 work. The first `npx` run may need network access to download the pinned CLI.

## 18. Security and repository hygiene

```powershell
git status --short
git diff --check
git diff --name-only --cached
git check-ignore .env evaluation/reports/local-check.json
rg -n --hidden -g "!.git/**" -g "!.env" -g "!frontend/node_modules/**" -g "!evaluation/reports/**" "sk-(proj-)?[A-Za-z0-9_-]{20,}" .
rg -n "import ragas|from ragas|import deepeval|from deepeval" backend/app
```

Expected:

- no whitespace errors;
- `.env` and generated evaluation reports are ignored;
- no credential-like value is found in tracked source;
- Ragas/DeepEval are absent from the runtime application path; and
- only intended local changes are present/staged.

## 19. Stop safely

Stop host Uvicorn/Vite terminals with `Ctrl+C`, then stop containers without deleting data:

```powershell
docker compose down
```

Do not run `docker compose down -v` unless you intentionally want to delete the local PostgreSQL volume, ingested corpus, and validation records.

## 20. Troubleshooting

- **Docker pipe/API error:** start Docker Desktop fully, wait for the engine, and reopen PowerShell if necessary.
- **Compose says `POSTGRES_PASSWORD` is missing:** create the root `.env` and rerun `docker compose config --quiet`.
- **Password fails after editing `.env`:** the existing PostgreSQL volume retains its original password; restore the original value or deliberately recreate only this project's local volume after accepting data loss.
- **Host database connection fails:** use `localhost:5433`, not container port 5432.
- **Alembic cannot find `DATABASE_URL`:** ensure the root `.env` contains the host URL and run Alembic from `backend` as documented.
- **Wrong migration head:** rerun `alembic upgrade head`; Phase 001–007 expects `20260920_0004`.
- **Live integration tests skip:** make PostgreSQL healthy, define `DATABASE_URL` in root `.env`, apply migrations, ingest the corpus, and rerun.
- **Ingestion/retrieval has no policy rows:** apply migrations, then rerun `scripts/ingest_policies.py` from the repository root.
- **`/ready` returns 503:** inspect `docker compose ps`, `docker compose logs postgres`, `docker compose logs redis`, and backend logs.
- **Port already allocated:** stop the host process/container using 8000, 5173, 5433, or 6379, or intentionally reconfigure both environment and commands.
- **Frontend cannot reach the API:** set `VITE_API_BASE_URL=http://localhost:8000`, align `CORS_ORIGINS`, and rebuild/restart the frontend.
- **Model endpoint returns 503:** verify the selected provider key is visible to the backend and restart it. Controlled failure is safer than fabricated output.
- **AI review summary is unavailable:** this is safe; deterministic facts and human review must remain usable.
- **Cohere reranking is unavailable:** use `RERANK_PROVIDER=rrf` for the deterministic smoke or configure a private Cohere key for a deliberate live test.
- **Windows async psycopg/checkpoint error:** use the implemented worker-thread `SelectorEventLoop` compatibility path; do not remove it from the application.
- **Duplicate final review returns 409:** expected after the first authoritative final action.
- **Evaluation gate fails:** inspect the named report/case, verify the exact six-document corpus and live database, and do not update thresholds merely to force a pass.
- **OpenSpec download stalls:** restore network access and keep CLI version `1.10.0` pinned.
- **Stale local environment:** continue using the documented `uv run --no-project --python 3.12 --with-requirements ...` commands instead of relying on a checked-in or old virtual environment.

## 21. Final acceptance checklist

Phase 001–007 local validation is complete only when:

- [ ] the validated branch, commit, and worktree state are recorded;
- [ ] PostgreSQL and Redis are healthy;
- [ ] Alembic is at `20260920_0004` and pgvector is installed;
- [ ] the corpus contains 6 ACTIVE documents and 50 chunks;
- [ ] PostgreSQL FTS and pgvector queries both return results;
- [ ] all focused Phase 001–007 tests pass, including live database modules;
- [ ] the complete current Python suite passes;
- [ ] both frontend tests and the production build pass;
- [ ] health, readiness, Swagger/OpenAPI, and UI checks pass;
- [ ] Policy Q&A either returns verified citations or safely abstains;
- [ ] expense clarification and idempotency preserve identity;
- [ ] deterministic evidence/rules produce the expected assessment;
- [ ] only an authorized human creates the final exception decision;
- [ ] business tables and audit events retain authoritative history;
- [ ] Model Gateway failures remain controlled and secrets remain isolated;
- [ ] deterministic Phase 007 metrics meet every configured gate;
- [ ] Ragas/DeepEval skip explicitly unless a live run was intentionally enabled;
- [ ] tracing is redacted and has no effect on business outcomes;
- [ ] all canonical OpenSpec specs validate and all Phase 001–007 archives have zero pending tasks; and
- [ ] no secret, `.env`, generated report, or unrelated file is staged.
