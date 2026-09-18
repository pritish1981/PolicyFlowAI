## 1. Contracts and business persistence

- [x] 1.1 Add strict expense intake, clarification, response, typed rule/rule-set, and decision schemas with Decimal money; verify unit tests cover enums, precision, missing versus invalid fields, and forbidden fields.
- [x] 1.2 Add the minimal Alembic migration for expense, assessment, idempotency, and logically separate checkpoint storage; verify upgrade/current and schema/index inspection against live PostgreSQL.
- [x] 1.3 Implement SQLAlchemy business models and short-transaction repository methods for creation, pending/failed/completed status, assessment, and replay; verify persistence and concurrency/idempotency tests.

## 2. Evidence and governed extraction

- [x] 2.1 Reuse hybrid retrieval with deterministic ACTIVE/date/model and category/region predicates across amount, documentation, and exception policies; verify split lexical/vector and multi-policy coverage tests.
- [x] 2.2 Reuse RRF, reranking, and authoritative citations with bounded evidence selection that retains critical rule coverage; verify source-ID, metadata, date, and no-evidence tests.
- [x] 2.3 Add `EXPENSE_POLICY_RULE` routing, evidence-only prompt, structured rule-set extraction, and numeric/source validation through the Model Gateway; verify fake-provider schema, unavailable, and malformed-result tests without live credentials.

## 3. Deterministic assessment and orchestration

- [x] 3.1 Implement a separately testable Decimal rule engine for amount, receipt, prohibition, exception, conflict, and missing-evidence cases; verify hotel/meal/taxi and receipt-boundary unit tests.
- [x] 3.2 Implement deterministic confidence/coverage and sanitized decision explanation; verify unsupported/mismatched evidence cannot yield a material decision.
- [x] 3.3 Extend the existing graph state and builder with the expense path, deterministic missing-field routing, retrieval/extraction/evaluation/citation/finalization stages, and no HITL transition; verify graph node-order and result tests with fakes.
- [x] 3.4 Persist compact clarification execution state, resume on the same thread after supplied fields, and preserve business/checkpoint separation; verify restart/resume and duplicate-clarification tests.
- [x] 3.5 Implement ExpenseService transaction boundaries and typed failure handling; verify expense is committed before model work, assessment after success, and controlled failed/pending state on errors.

## 4. API and React delivery

- [x] 4.1 Register thin `POST /api/v1/expenses` and clarification route with request/thread IDs, idempotency header, 422/409/503 mapping; verify OpenAPI and API integration tests for all decision/clarification/replay paths.
- [x] 4.2 Add typed expense API client and accessible form with validation, loading/error, missing-field correction, and Decimal strings; verify TypeScript production build.
- [x] 4.3 Add assessment view with all four decisions, limit/confidence/next action, and stored citation details; verify no pending review is displayed as approval and responsive build/manual inspection.

## 5. Golden cases and final verification

- [x] 5.1 Expand deterministic expense golden cases for domestic/international hotel, meal, taxi, receipt, no evidence, and conflicts; verify dataset schema and expected source lineage tests.
- [x] 5.2 Run targeted and full credential-free backend tests and fix in-scope regressions; record exact command/result and ensure existing Phase 003 tests pass.
- [x] 5.3 Run live PostgreSQL migration, RAG eligibility/retrieval and persistence smoke using the project environment; report exact revision and any unavailable external-provider limitation.
- [x] 5.4 Run frontend build and manual API/UI checks where available; report exact results and any unverified browser behavior.
- [x] 5.5 Validate `004-expense-compliance-assessment`, specs, and all OpenSpec scopes strictly; mark only verified tasks complete and report remaining work truthfully.
