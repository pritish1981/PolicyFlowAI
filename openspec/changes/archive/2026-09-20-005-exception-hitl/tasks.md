## 1. Contracts and authoritative persistence

- [x] 1.1 Add strict exception justification, follow-up, review action, summary, queue/detail, and outcome schemas with bounded text, enums, Decimal values, and forbidden extra fields; verify unit tests cover valid and invalid values and prove the summary schema has no authoritative decision field.
- [x] 1.2 Add the minimal Alembic revision for `app.exception_request`, `app.review`, and `app.audit_event` with foreign keys, status checks, timestamps, indexes, and final-review uniqueness; verify upgrade/current and live schema/constraint inspection without recreating Phase 004 or RAG tables.
- [x] 1.3 Implement SQLAlchemy models and relationships for exception, review history, and append-only audit events; verify model metadata and persistence tests match the migration.
- [x] 1.4 Implement repository reads for exception eligibility, current outcome, pending queue, reviewer detail, and citation resolution; verify ineligible/missing/finalized and minimum-data projection tests.
- [x] 1.5 Implement row-locked atomic reviewer transactions for action insert, exception/expense transition, and audit append, with at most one final action; verify concurrent or repeated finalization yields one success and HTTP 409 semantics for the loser.

## 2. Deterministic context and governed summary

- [x] 2.1 Implement exception eligibility and justification validation against the persisted Phase 004 assessment and active exception state; verify only `NEEDS_REVIEW` can create one controlled exception.
- [x] 2.2 Implement Decimal variance from authoritative expense amount and evidenced policy limit, retaining null without a numeric limit; verify `9500.00 - 7000.00 = 2500.00`, precision, and null cases.
- [x] 2.3 Reuse stored Phase 004 citations and confirm their authoritative chunk metadata remains resolvable before review presentation; verify invalid/unavailable citations are not fabricated or replaced through a new retrieval path.
- [x] 2.4 Add `EXCEPTION_REVIEW_SUMMARY` routing, versioned neutral prompt, structured output, citation-subset validation, and sanitized usage telemetry through the existing Model Gateway; verify fake-provider success, invalid citations, decision-like output rejection, and no live credential requirement.
- [x] 2.5 Persist summary success or `UNAVAILABLE` independently of exception authority and allow review to continue on provider/schema failure; verify model failure does not corrupt or block a legitimate pending case.

## 3. LangGraph interrupt and resume

- [x] 3.1 Extend the compact expense state and existing graph builder for exception IDs, justification, variance, summary, reviewer payload, and errors without storing full policy documents; verify state serialization contains only bounded review context.
- [x] 3.2 Implement `collect_exception` to reload authoritative Phase 004 facts, validate eligibility, compute variance, prepare/persist review context, and route to human review without deciding; verify node tests cover eligible, ineligible, and summary-failure paths.
- [x] 3.3 Implement `human_review` with LangGraph `interrupt()` and a bounded payload containing the persisted exception, expense facts, policy rule, variance, justification, summary status, and verified citations; verify the graph returns an interrupt for `NEEDS_REVIEW` exception submission.
- [x] 3.4 Reuse `AsyncPostgresSaver`, the existing Windows SelectorEventLoop compatibility path, and the original expense `thread_id`; verify a checkpointed interrupt survives graph/service recreation in live PostgreSQL.
- [x] 3.5 Implement same-thread `Command(resume=...)` handling for APPROVE, REJECT, and REQUEST_MORE_INFORMATION plus deterministic final workflow output; verify each graph branch reaches its specified end/continuation without changing the human action.
- [x] 3.6 Make post-commit graph resume idempotently retryable so business truth survives checkpoint/runtime failure; verify retry does not insert a duplicate review or audit outcome.

## 4. Services, APIs, and audit

- [x] 4.1 Implement the exception submission service and `POST /api/v1/expenses/{expense_id}/exceptions` with request correlation, controlled duplicate handling, short transactions, summary fallback, and interrupt invocation; verify 201/200, 404, 409, 422, and controlled 503 API tests.
- [x] 4.2 Implement demo employee/reviewer identity and role dependencies with 403 enforcement; verify reviewer endpoints reject an employee role and employee mutation endpoints reject a reviewer-only mismatch where applicable.
- [x] 4.3 Implement `GET /api/v1/reviews/pending` and `GET /api/v1/reviews/{exception_id}` with minimal authoritative projections and server-side citation excerpts; verify pending filtering, detail completeness, and no checkpoint/internal secret exposure.
- [x] 4.4 Implement `POST /api/v1/reviews/{exception_id}/decision` with schema validation, authoritative transaction, audit, and same-thread resume; verify APPROVE, REJECT, REQUEST_MORE_INFORMATION, invalid decision, and duplicate conflict API tests.
- [x] 4.5 Implement `POST /api/v1/exceptions/{exception_id}/information` to append valid employee follow-up, preserve IDs/history, and return the case to the same-thread `PENDING_REVIEW` interrupt; verify invalid-state conflict and a later final decision.
- [x] 4.6 Extend expense retrieval/response behavior to expose current exception and reviewer outcome separately from the immutable Phase 004 assessment; verify approved/rejected/pending/more-information states never rewrite `assessment.decision`.
- [x] 4.7 Register routes and append sanitized exception-created, interrupted, reviewer-action, information-provided, resumed, and finalized audit events with correlation/state transitions; verify audit reconstruction works without checkpoint tables.

## 5. Employee and reviewer frontend

- [x] 5.1 Add typed exception/review API contracts and clients with controlled error handling and demo role headers; verify TypeScript checks cover all statuses and reviewer decisions.
- [x] 5.2 Extend the expense result with justification submission, pending/final outcome, requested-information input, verified citations, and explicit non-authoritative summary labeling; verify UI tests prevent pending or AI text from appearing as approval.
- [x] 5.3 Add a reviewer queue and detail/action view with expense/policy/variance/justification/summary evidence, comments, three actions, loading/error states, and duplicate-submit protection; verify frontend tests exercise APPROVE, REJECT, and REQUEST_MORE_INFORMATION.
- [x] 5.4 Integrate navigation and responsive styles without regressing Policy Q&A or Phase 004 assessment screens; verify the production build and available browser/manual checks.

## 6. End-to-end verification and documentation

- [x] 6.1 Add credential-free unit, repository/service, graph, and API integration coverage for eligibility, validation, variance, summary safety/fallback, all transitions, concurrent finalization, and audit; run targeted and full backend test suites and record exact results.
- [x] 6.2 Run Alembic upgrade/current and a live PostgreSQL HITL smoke for POST exception, pending/detail, persisted interrupt, service recreation, APPROVE and REJECT finalization, plus REQUEST_MORE_INFORMATION round-trip; record revision, business rows, checkpoint evidence, and exact failures if infrastructure is unavailable.
- [x] 6.3 Run frontend tests/lint/build and manually verify the INR 9500 hotel versus INR 7000 policy demo across APPROVE, REJECT, and REQUEST_MORE_INFORMATION where browser access is available; report any unverified visual gate truthfully.
- [x] 6.4 Update the root README with Phase 005 scope, architecture boundary, startup/migration commands, role headers, API/UI validation, expected outcomes, checkpoint/business separation, troubleshooting, and explicit Phase 006+ deferrals; verify every command/path against the checkout.
- [x] 6.5 Run strict validation for `005-exception-hitl`, specs, and all OpenSpec scopes; mark only fully evidenced tasks complete, confirm no secrets or unrelated untracked files are included, and stop without beginning Phase 006 or archiving.
