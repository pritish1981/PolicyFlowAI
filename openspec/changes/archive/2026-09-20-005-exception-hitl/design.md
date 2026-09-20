## Context

See `proposal.md` and the two delta specs. Phase 004 already persists `app.expense` and one `app.assessment`, records Decimal amount and policy limit, returns verified citations, assigns a unique stable `thread_id`, and invokes the expense graph with `AsyncPostgresSaver` in the logically separate `checkpoint` schema. Its graph currently ends after `decide`; exception/review/audit models, repositories, services, routes, and the `collect_exception`, `human_review`, `finalize_decision`, and `audit_event` node modules are placeholders. The frontend has one expense assessment page, and reviewer routes are not registered.

FRD v1.0 and the HLD/LLD require human-owned APPROVE, REJECT, or REQUEST_MORE_INFORMATION actions, same-thread interrupt/resume, and separation of business truth from checkpoint state. The existing LangGraph/PostgreSQL and Windows SelectorEventLoop compatibility path must be reused. Phase 004's assessment and citations are authoritative inputs; Phase 005 must not rerun compliance decision logic or create a second RAG path.

## Goals / Non-Goals

**Goals:** Complete UC-03 with durable exception/review/audit records, deterministic variance, safe summary assistance, PostgreSQL interrupt/resume, atomic human finalization, a minimal follow-up loop, and employee/reviewer UI. Keep automated tests credential-free and prove restart-resume behavior against live PostgreSQL where available.

**Non-Goals:** Replace the Phase 004 assessment, let a model approve or reject, implement settlement, enterprise identity, notifications, OCR/fraud, multi-agent coordination, broad gateway hardening, full evaluation dashboards, or deployment work.

## Decisions

### 1. Preserve the Phase 004 assessment and add a separate human outcome

`app.assessment.decision` remains `NEEDS_REVIEW`; a later review changes `app.exception_request.status` and a separate final expense workflow status, not the historical deterministic assessment. This preserves traceability between policy evaluation and human exception authority. Rewriting the assessment was rejected because it would erase which result triggered review.

### 2. Add minimal normalized business records and append-only audit

Create one migration after `20260917_0003` with `app.exception_request`, `app.review`, and `app.audit_event`. The exception has unique `assessment_id` and links to expense, stable thread, justification/follow-up history, Decimal variance, summary JSON/status, and constrained lifecycle status. Each reviewer action is an immutable row; multiple rows are allowed only to support REQUEST_MORE_INFORMATION followed by a later final action. A partial unique constraint permits at most one APPROVE/REJECT action per exception. Audit rows store event type, correlation IDs, actor, transition metadata, and timestamp without full policy text or secrets.

Alternative single-table review state was rejected because it would overwrite history. Checkpoint tables are not queried for reporting or authoritative decisions.

### 3. Short transactions bracket graph work

Exception submission transaction locks/validates expense and assessment, creates or returns the controlled exception, and commits before model or graph work. Summary generation is outside the business transaction; its result/failure is stored in a short update. The graph then enters `human_review` and checkpoints its interrupt.

A reviewer action transaction locks the exception, validates `PENDING_REVIEW`, inserts the review, changes exception/expense workflow status, and appends audit atomically. Graph resume happens after commit with the same `thread_id`. If resume fails, business truth remains committed and an idempotent retry/reconciliation path resumes from the recorded action without inserting another review. Holding a database transaction open across LangGraph/model I/O was rejected because it increases lock time and couples business durability to external execution.

### 4. Extend the existing expense graph with an exception entry/resume path

Extend `ExpenseState` with compact exception and reviewer fields and extend the existing expense graph builder rather than creating another graph. An exception submission invokes the graph on the original thread with the persisted Phase 004 context and routes through `collect_exception` to `human_review`. `human_review` calls LangGraph `interrupt()` with a bounded, server-built payload. Review resume uses the installed LangGraph `Command(resume=...)` API and original `thread_id`; `finalize_decision` mirrors the already-authoritative reviewer action into workflow output and `audit_event` records execution telemetry.

For REQUEST_MORE_INFORMATION, the reviewer action is committed and the resumed graph returns a controlled `PROVIDE_MORE_INFORMATION` outcome. Employee follow-up appends information, transitions the same exception to `PENDING_REVIEW`, and re-enters the human-review interrupt on the same thread. This provides one repeatable loop without designing a general case-management engine.

### 5. Use Phase 004 facts and citations; do not retrieve again

`collect_exception` reloads the authoritative expense and assessment, verifies `NEEDS_REVIEW`, validates justification, computes `amount - policy_limit` with Decimal when a limit exists, and uses stored verified citations after confirming their chunk metadata is still resolvable. Large policy documents are never copied into checkpoints. This avoids drift between assessment evidence and review evidence and avoids duplicate RAG logic.

### 6. Add a bounded summary task with fail-open-to-human behavior

Add `ModelTask.EXCEPTION_REVIEW_SUMMARY`, a versioned evidence-only prompt, and `ExceptionReviewSummary` containing summary text, key facts, attention points, and supplied citation UUIDs. Schema and citation-subset validation prohibit an authoritative decision field. The UI labels it non-authoritative. Provider/schema failure stores `UNAVAILABLE`, emits sanitized telemetry, and continues to human review using deterministic facts. Fabricating a fallback summary was rejected.

### 7. Keep API authorization explicit and minimal

Use the existing dependency/router style with a small demo-role header abstraction: employee actions require EMPLOYEE and reviewer list/detail/decision require REVIEWER, returning 403 on mismatch. Endpoints are:

- `POST /api/v1/expenses/{expense_id}/exceptions`
- `POST /api/v1/exceptions/{exception_id}/information`
- `GET /api/v1/expenses/{expense_id}` extended with exception outcome
- `GET /api/v1/reviews/pending`
- `GET /api/v1/reviews/{exception_id}`
- `POST /api/v1/reviews/{exception_id}/decision`

Pydantic bounds justification/comments, uses enums for decisions/status, and returns 404, 409, 422, or controlled 503 consistently. Reviewer identity comes from the demo identity abstraction rather than trusting an arbitrary payload field when the header is available.

### 8. UI shares typed contracts but separates employee and reviewer concerns

Extend the expense page with justification, follow-up, and status panels. Add a reviewer route/page with pending queue, selected-case detail, verified citations, summary labeling, comment input, and the three actions. Disable duplicate submission during requests and refresh from authoritative API responses. This remains a POC role switch, not SSO or advanced RBAC.

### 9. Verification follows business/checkpoint separation

Unit tests cover eligibility, string bounds, Decimal variance, schemas, citation subset, and state transitions. Service/API tests cover persistence, role checks, summary failure, queue/detail, all actions, follow-up, and conflict handling with fakes. Graph tests prove interrupt payload and each resume branch; live PostgreSQL integration proves checkpoint survival after graph/service recreation and inspects business records independently. Frontend tests/build cover employee and reviewer flows. OpenSpec validation, Alembic current/upgrade, full backend checks, and README runbook updates close the change.

## Design Reconciliation / Decision Required

- **FRD illustrative float versus current Phase 004 Decimal:** retain Decimal/NUMERIC for amount, limit, and variance.
- **FRD combined assessment-to-HITL graph versus Phase 004 committed stop:** enter the same graph/thread from the persisted `NEEDS_REVIEW` assessment; do not recompute the assessment or silently create a new thread.
- **Business commit versus graph resume ordering:** commit the human action first, then resume idempotently. This keeps business tables authoritative if checkpoint resume fails.
- **Suggested review uniqueness versus required information rounds:** permit multiple immutable review actions but enforce at most one final APPROVE/REJECT and require `PENDING_REVIEW` under row lock for every action.
- **Reviewer ID in example payload versus demo auth boundary:** derive reviewer identity from the demo role/identity dependency where present; do not accept identity only as untrusted request data.

## Risks / Trade-offs

- **Business decision commits but resume fails** -> Store the review action and resume status, return a controlled retryable result, and make resume idempotent without duplicating business rows.
- **Two reviewers race** -> Lock the exception, check status inside the transaction, and enforce database uniqueness for a final review.
- **Stored citations become unavailable** -> Show only currently resolvable stored metadata, record the condition, and do not ask the model to replace missing evidence.
- **Summary provider fails** -> Continue human review with summary unavailable; never convert model failure into approval or denial.
- **Checkpoint state grows** -> Persist identifiers, compact facts, summary, and citation metadata only; keep source documents in authoritative stores.
- **Demo role headers are not production identity** -> Clearly document the POC boundary and defer SSO/RBAC hardening.

## Migration Plan

1. Strictly validate the Phase 005 planning artifacts before application code.
2. Add and apply the minimal business migration after confirming the current live revision; never recreate expense, assessment, policy, or checkpoint tables.
3. Implement schemas, repositories, deterministic context/summary, graph interrupt/resume, services/APIs, audit, and UI incrementally with credential-free tests.
4. Run targeted and full backend tests, live PostgreSQL migration/checkpoint/restart smoke, frontend tests/build, and strict OpenSpec validation; update README and task checkboxes only from verified evidence.
5. Rollback hides the Phase 005 routes/UI and stops new actions first. Preserve business/audit records before downgrading; drop only Phase 005 tables/constraints during a deliberate database downgrade. Existing Phase 004 assessment and RAG data remain intact.
