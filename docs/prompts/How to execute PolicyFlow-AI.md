# How to execute and validate PolicyFlow AI (Phases 001-004)

This is the consolidated local runbook for platform, policy ingestion and retrieval, Policy Q&A, and Phase 004 expense assessment. Run commands from `D:\git-repo\PolicyFlow-AI` unless a step changes directories. Phase 004 is implemented and its OpenSpec change is archived; the working-tree changes have not been committed or published. Automated tests use fake model providers. Real Policy Q&A and expense rule extraction require a working `OPENAI_API_KEY`.

## 1. Check prerequisites and local configuration

Use Docker Desktop, Python 3.12 with `uv`, Node.js 20 with npm, and PowerShell. Confirm you are validating the intended checkout:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI
git status --short
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose config --quiet
```

In `.env`, set `POSTGRES_PASSWORD`, a matching host `DATABASE_URL` using `localhost:5433`, and `REDIS_URL=redis://localhost:6379/0`. For a fast retrieval smoke, use `RERANK_PROVIDER=rrf`; this checks RRF ordering, not a semantic reranker. To test the real model path, set `OPENAI_API_KEY` before starting the backend. Never print or commit secrets. The commands below use `uv run --no-project --with-requirements` so a stale root or backend `.venv` does not hide missing packages.

## 2. Start infrastructure and migrate

```powershell
docker compose up -d postgres redis
docker compose ps
docker compose exec -T postgres pg_isready -U policyflow -d policyflow
docker compose exec -T redis redis-cli ping
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic upgrade head
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m alembic current
Pop-Location
```

Expect PostgreSQL to accept connections, Redis to return `PONG`, and Alembic to report `20260917_0003 (head)`. This supersedes the Phase 003 head `20260913_0002`. If your `.env` changes `POSTGRES_USER` or `POSTGRES_DB`, substitute those values in the `docker compose exec` commands.

Check the authoritative business tables and checkpoint schema:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='app' AND table_name IN ('expense','assessment','expense_idempotency') ORDER BY table_name"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name='checkpoint'"
```

Expect three `app` table names and `checkpoint`. Expense and assessment are separate business records; checkpoint data is workflow state.

## 3. Ingest and verify synthetic evidence

```powershell
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
uv run --no-project --python 3.12 --with-requirements backend/requirements.txt python scripts/ingest_policies.py
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_document"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk"
```

On a fresh database the first ingestion indexes `POL-001` through `POL-006`; the second reports `unchanged`. Expect 6 documents and 50 chunks. If you already have these records, both runs can report `unchanged`.

Confirm that both PostgreSQL retrieval paths have indexed evidence:

```powershell
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT count(*) FROM rag.policy_chunk WHERE search_vector @@ websearch_to_tsquery('english', 'hotel')"
docker compose exec -T postgres psql -U policyflow -d policyflow -tAc "SELECT id FROM rag.policy_chunk ORDER BY embedding <=> (SELECT embedding FROM rag.policy_chunk LIMIT 1) LIMIT 3"
```

The full-text count should be positive and the vector query should return three chunk IDs.

## 4. Run backend checks with no model credentials

```powershell
Push-Location backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q tests/test_expense_schema.py tests/test_expense_rules.py tests/test_expense_evidence.py tests/test_expense_rule_extraction.py tests/test_expense_api.py tests/test_policy_qa.py
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m pytest -q
Pop-Location
```

The latest verified results for this checkout were **48 targeted** and **64 full-suite** passes. The full suite needs live PostgreSQL and the six-policy corpus. It checks migration/repository persistence, idempotency and concurrency, same-thread clarification, live FTS and pgvector retrieval, verified citations, fake-provider hotel/meal/taxi decisions, and Phase 003 Q&A regressions. A different count after later edits is not automatically a failure; every test must pass.

## 5. Start the backend and inspect the API

In a separate PowerShell terminal:

```powershell
Set-Location D:\git-repo\PolicyFlow-AI\backend
uv run --no-project --python 3.12 --with-requirements requirements.txt python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

From another terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
$openapi = Invoke-RestMethod http://localhost:8000/openapi.json
$openapi.paths.'/api/v1/expenses'.post.operationId
$openapi.paths.'/api/v1/expenses/{expense_id}/clarifications'.post.operationId
```

Expect health `ok`, readiness `ready`, and both expense operations. Swagger UI is at `http://localhost:8000/docs`.

Also check `$openapi.paths.'/api/v1/policy/query'.post.operationId` for the Policy Q&A operation. In Swagger UI, confirm the health, readiness, policy ingestion, policy query, expense creation, and clarification routes appear.

### Policy Q&A smoke

With a working `OPENAI_API_KEY`, submit a policy question:

```powershell
$question = @{ question='What is the maximum hotel reimbursement allowed for domestic travel?'; category='HOTEL'; region='INDIA' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/policy/query -Headers @{ 'X-Request-ID'='local-policy-qa-001' } -ContentType 'application/json' -Body $question | ConvertTo-Json -Depth 6
```

When the provider succeeds and evidence supports the answer, expect `GROUNDED` with a verified `POL-002` citation. Without a working model key, expect a controlled HTTP 503. The credential-free tests in step 4 cover grounded answers and safe abstention without provider credentials.

## 6. Verify clarification and idempotency without a model key

This request omits `purpose` and `receipt_available`, so it should stop before retrieval or model use:

```powershell
$key = [guid]::NewGuid().ToString()
$headers = @{ 'Idempotency-Key' = $key; 'X-Request-ID' = 'phase004-local-clarification' }
$body = @{ expense_type='HOTEL'; amount='6500.00'; currency='INR'; location='Bengaluru'; travel_type='DOMESTIC' } | ConvertTo-Json
$first = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $headers -ContentType 'application/json' -Body $body
$replay = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers $headers -ContentType 'application/json' -Body $body
$first | ConvertTo-Json -Depth 6
$first.expense_id -eq $replay.expense_id
$first.thread_id -eq $replay.thread_id
```

Expect `INSUFFICIENT_INFORMATION`, `PROVIDE_CLARIFICATION`, both missing field names, and two `True` comparisons. Supply one missing value:

```powershell
$partial = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/expenses/$($first.expense_id)/clarifications" -ContentType 'application/json' -Body (@{ purpose='Client meeting' } | ConvertTo-Json)
$partial | ConvertTo-Json -Depth 6
$partial.thread_id -eq $first.thread_id
```

Expect the same expense/thread, with only `receipt_available` still missing. Completing the last field starts model extraction; without a configured key, the API returns a controlled HTTP 503 and keeps the expense in a failed state for a retry with the same idempotency key after the provider is configured.

## 7. Optionally verify live expense decisions

Set a working `OPENAI_API_KEY` in `.env` and restart the backend. A configured provider and eligible policy evidence are required. Use a fresh key for each different request:

```powershell
$hotel = @{ expense_type='HOTEL'; amount='6500.00'; currency='INR'; location='Bengaluru'; travel_type='DOMESTIC'; purpose='Client meeting'; receipt_available=$true } | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/expenses -Headers @{ 'Idempotency-Key' = [guid]::NewGuid().ToString() } -ContentType 'application/json' -Body $hotel
$result | ConvertTo-Json -Depth 8
```

With supported POL-002 and POL-005 evidence and successful structured extraction, expect `COMPLIANT`, policy limit `7000.00`, and verified citations. Repeat with amount `9500.00` and a new key: expect `NEEDS_REVIEW`, limit `7000.00`, and `SUBMIT_EXCEPTION_JUSTIFICATION`; this does not start human review. A missing receipt above INR 500 with verified POL-005 evidence should yield `NON_COMPLIANT`. If no valid evidence applies, expect `INSUFFICIENT_INFORMATION` with no invented limit. The deterministic fake-provider integration tests in step 4 are the reproducible decision proof; a live provider can return a controlled 503 when unavailable or unable to produce a valid rule set.

## 8. Build and inspect the frontend

```powershell
Push-Location frontend
npm.cmd ci
npm.cmd run build
$env:VITE_API_BASE_URL = 'http://localhost:8000'
npm.cmd run dev -- --host localhost
```

Open `http://localhost:5173`. Check the three status cards and the Policy Q&A form: ask the domestic hotel question, inspect the citation details, try an unsupported question for insufficient information, and confirm a one-character question is rejected. Then inspect **Assess an expense**. Submit the incomplete hotel request from step 6 and confirm the missing fields appear. Complete it with a configured model provider, then check the decision, limit, confidence, next action, and stored citation details. Try a second expense in the same page session; it should use a fresh idempotency key. Check a narrow viewport for clipping and confirm `NEEDS_REVIEW` is presented as requiring human review, not approval. The frontend has no separate test runner; `npm.cmd run build` is its automated gate. If the model key is absent, a complete question or expense should show a controlled temporary-unavailable error rather than a fabricated result.

Stop the Vite process with Ctrl+C, then return to the root with `Pop-Location`.

### Additional policy questions to inspect

- POL-001: What general conditions must a business-travel expense satisfy? Which rule takes precedence when a category-specific policy is more specific?
- POL-002: What are the standard domestic and international hotel-room limits? Does a domestic INR 9,500 room charge receive automatic approval?
- POL-003: Is the domestic meal allowance INR 1,500 per meal or per day? Are alcoholic beverages covered?
- POL-004: What is the eligible airport taxi limit within India? Is sightseeing transport reimbursable?
- POL-005: Is a receipt mandatory at exactly INR 500 or only above INR 500? Can a clear digital receipt satisfy the rule? Does a receipt alone establish business purpose?
- POL-006: Can PolicyFlow AI approve an exception by itself? What must an employee provide before human review, and what can a reviewer decide?

Check each answer against the cited policy section. A policy answer describes the rule; it does not approve a specific expense or exception.

## 9. Validate OpenSpec and inspect final status

```powershell
npx.cmd -y @fission-ai/openspec@1.10.0 validate --specs --strict
npx.cmd -y @fission-ai/openspec@1.10.0 validate --all --strict
npx.cmd -y @fission-ai/openspec@1.10.0 list --json
Test-Path openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/tasks.md
(Select-String -Path openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/tasks.md -Pattern '^- \[x\]').Count
git status --short
```

For this working tree, expect 4 canonical specs to pass and `validate --all --strict` to report 4 passed and 0 failed. `list --json` should report no active changes. The archive task file should exist and contain 19 completed tasks. Phase 003 is also archived with 27/27 tasks. The working tree still contains uncommitted Phase 004 files; validation and archiving do not commit or publish them.

## Troubleshooting and scope

- If `uv` reports access denied in a managed environment, run the terminal with the required local permission. If a `.venv` points to a missing Python installation, use the `--no-project --with-requirements` commands above.
- If backend tests stall or `/ready` returns 503, check `docker compose ps`, `.env` host port `5433`, migration head, and corpus counts. Do not run a migration downgrade on a database containing business records.
- If the model call returns 503, check the key visible to the backend process and restart it after changing `.env`. Credential-free tests can still validate the decision path.
- `RERANK_PROVIDER=rrf` is useful for a fast smoke; use configured Cohere or local BGE separately when you need to validate semantic reranking.
- Phase 004 records `NEEDS_REVIEW` and a next action. Reviewer queue, approval/rejection, exception justification, and reimbursement remain later-phase work.
