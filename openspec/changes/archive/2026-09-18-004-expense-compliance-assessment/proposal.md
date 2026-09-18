## Why

PolicyFlow AI can answer policy questions, but employees cannot submit a structured expense and receive an auditable assessment. Phase 004 adds this use case while keeping expense records and compliance decisions under deterministic application control.

## What Changes

- Add `POST /api/v1/expenses` with Decimal money, targeted clarification for missing assessment facts, idempotency, and a persisted expense and assessment.
- Extend the existing LangGraph orchestration with an `expense_assessment` path that reuses eligible PostgreSQL full-text and pgvector retrieval, RRF, reranking, and authoritative citation validation.
- Add a governed `EXPENSE_POLICY_RULE` Model Gateway task to extract structured rules only. Deterministic code evaluates amount, receipt, prohibition, exception routing, evidence sufficiency, and confidence.
- Add a React expense form and assessment result view with verified citations and controlled error/clarification states.
- Add a business-schema migration, credential-free unit/API/graph/service tests, a synthetic expense-case dataset, and local migration/retrieval/build verification.
- Stop `NEEDS_REVIEW` after recording the assessment and returning a next action; do not enter human review in Phase 004.

## Capabilities

### New Capabilities

- `expense-compliance`: Structured expense intake, authoritative persistence, evidence-grounded deterministic assessment, clarification, idempotency, and UI presentation.

### Modified Capabilities

None. Phase 004 consumes the existing hybrid RAG, Policy Q&A, and Model Gateway contracts without changing their externally observable requirements.

## Impact

- **API and schemas:** `POST /api/v1/expenses`, expense/assessment response contracts, HTTP 422/409/503 behavior, request and thread correlation.
- **Business data:** new `app.expense`, `app.assessment`, and bounded idempotency storage with Alembic migration; no duplicate RAG tables.
- **Orchestration:** an expense path in the existing graph module and compact expense state, with no Phase 005 reviewer transition.
- **Policy and model:** reuse of Phase 002/003 retrieval and citations; structured rule extraction through the central gateway; deterministic rule and confidence controls.
- **Frontend and verification:** expense entry/results, synthetic golden cases, credential-free tests, frontend build, live PostgreSQL migration/retrieval checks, and strict OpenSpec validation.

## Out of Scope

Exception justification, reviewer actions and UI, human interrupt/resume, payment, OCR, fraud, deployment, full evaluation dashboards, and autonomous approvals.
