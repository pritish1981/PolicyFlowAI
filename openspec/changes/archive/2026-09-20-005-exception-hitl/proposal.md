## Why

Phase 004 stops an evidence-grounded, deterministic expense assessment at `NEEDS_REVIEW`, but PolicyFlow AI does not yet let an employee justify the exception or let an authorized reviewer resolve it. Phase 005 completes the FRD UC-03 boundary with durable business records and resumable human review while ensuring that AI remains non-authoritative.

## What Changes

- Accept an employee justification only for an existing assessment whose decision is `NEEDS_REVIEW`, calculate any policy-limit variance with Decimal arithmetic, and persist one controlled exception request.
- Extend the existing expense LangGraph with exception collection, a `human_review` interrupt, same-thread PostgreSQL checkpoint resume, deterministic finalization, and a minimal more-information loop.
- Add authoritative exception, reviewer-action, and audit persistence with row locking, status checks, atomic finalization, and duplicate-decision conflict handling.
- Add a governed `EXCEPTION_REVIEW_SUMMARY` Model Gateway task that neutrally summarizes supplied expense facts, justification, variance, and verified citations without recommending or making a decision; summary failure does not block legitimate review.
- Add employee exception submission and status UI plus a demo-role reviewer queue, detail view, and APPROVE, REJECT, or REQUEST_MORE_INFORMATION actions.
- Add credential-free unit, service, graph, API, migration, and frontend verification for interrupt/restart/resume and all reviewer outcomes.
- Keep Phase 006 gateway hardening, Phase 007 evaluation/observability expansion, Phase 008 deployment, autonomous approval, payment, SSO, notifications, OCR, fraud, and multi-agent behavior out of scope.

## Capabilities

### New Capabilities

- `exception-review`: Employee exception justification, authoritative review records, evidence-grounded non-authoritative summary, durable LangGraph interrupt/resume, human reviewer decisions, more-information continuation, auditability, and employee/reviewer interfaces.

### Modified Capabilities

- `expense-compliance`: A persisted `NEEDS_REVIEW` assessment can enter controlled exception review and expose its later human-owned outcome without changing the deterministic Phase 004 assessment decision.

## Impact

- **API and schemas:** exception submission and clarification, pending/detail review queries, reviewer decision, and current expense/exception outcome contracts with demo employee/reviewer role checks.
- **Business data:** one Alembic revision for `app.exception_request`, `app.review`, and append-only `app.audit_event` storage or equivalent existing structures, with foreign keys, status constraints, timestamps, and concurrency protection.
- **Orchestration:** the existing expense graph/state gains exception collection, interrupt, same-thread resume, deterministic finalization, and audit stages; checkpoint data remains non-authoritative.
- **Model and evidence:** the central gateway gains a bounded summary task that uses Phase 004 facts and verified citation IDs; no new retrieval path or compliance decision logic is introduced.
- **Frontend:** the expense result supports justification and follow-up information; a reviewer experience supports pending queue, evidence detail, and controlled decisions.
- **Verification and docs:** tests cover eligibility, validation, variance, summary safety/fallback, persistence, concurrency, graph checkpoint recovery, API/UI behavior, and README local validation.
