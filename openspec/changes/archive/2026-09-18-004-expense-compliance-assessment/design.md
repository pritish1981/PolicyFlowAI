## Context

See `proposal.md` and `specs/expense-compliance/spec.md`. The current `PolicyQAState` and graph support only Q&A. Expense routes, service, models, repositories, and graph node modules are placeholders; Alembic has only schema bootstrap and RAG tables. Phase 003 already supplies `retrieve`, RRF, reranking, Model Gateway, and authoritative citation validation. The frontend has only a Q&A page.

FRD v1.0 defines UC-02 and FR-02/03/08/09 with authoritative business records and clarification continuity. HLD/LLD separate LangGraph execution state from `app` business tables. The LLD sample uses Decimal money, whereas the FRD's illustrative state uses float; Decimal/NUMERIC controls monetary evaluation. Phase 005 owns exception justification and human interrupt/resume, so a Phase 004 `NEEDS_REVIEW` assessment stops with a next action.

## Goals / Non-Goals

**Goals:** Implement a credential-free testable assessment path without regressing Q&A; keep policy limits in verified evidence, model extraction bounded, and financial conclusions deterministic. Commit an expense before model work, and an assessment after it. Preserve a stable thread across missing-field clarification.

**Non-Goals:** Implement reviewer/exception state transitions, payment, OCR, a general policy interpreter, or a live-provider CI gate.

## Decisions

### 1. Intake and clarification contracts

Use a strict Pydantic intake model that permits omission of the seven assessment fields but validates supplied enum, amount, precision, and text values. An absent field creates a pending record and an `INSUFFICIENT_INFORMATION` response with `missing_fields` and `PROVIDE_CLARIFICATION`. A separate `POST /api/v1/expenses/{id}/clarifications` accepts only missing/updated assessment fields, retains `expense_id` and `thread_id`, and continues the assessment once complete. Invalid supplied values and extra fields remain HTTP 422. This resolves the strict-create example against FRD-required clarification without turning malformed values into missing ones. The React form exposes these fields and offers correction under the same expense.

### 2. Business schema and transaction boundaries

Add one Alembic revision after `20260913_0002` with `app.expense` (UUID, nullable intake fields while pending, `NUMERIC(12,2)`, status, thread ID, timestamps), `app.assessment` (UUID/FK, decision, rule/citation JSONB, NUMERIC confidence/limit, explanation, model lineage, timestamps), and `app.expense_idempotency` (unique key, canonical request hash, expense ID). `ExpenseRepository` owns short transactions: insert expense/key and commit, invoke graph without an open business transaction, then insert assessment/update status and commit. Failure marks `ASSESSMENT_FAILED` in a separate transaction. Replays read persisted response; a concurrent in-progress replay gets the same expense with a controlled pending result. A conflicting hash returns 409. No RAG table is recreated.

### 3. Orchestration and clarification state

Extend `backend/app/graph/state.py` and the existing graph builder module with an `expense_assessment` route while retaining the Q&A route and its tests. The expense path validates state, detects missing fields, constructs filters, retrieves, fuses, reranks, extracts rules, validates citations, evaluates deterministic rules/confidence, finalizes, and logs. State stores identifiers, compact expense fields and selected evidence, not source documents beyond the transient retrieval stage. A PostgreSQL LangGraph checkpointer in a logically distinct schema retains pending clarification execution; business records remain authoritative. The clarification endpoint resumes the same thread. No `human_review` node is activated.

### 4. Multi-policy retrieval and verified rule extraction

Map HOTEL to HOTEL, MEAL to MEAL, TAXI to GROUND_TRANSPORTATION. Query category evidence plus DOCUMENTATION and EXPENSE_EXCEPTION in independent calls to the existing `retrieve` path. Every call keeps ACTIVE, effective/expiry, embedding-model, and compatible region predicates; GLOBAL policy remains eligible. Merge and deduplicate by chunk ID, use existing RRF and reranker, and reserve relevant evidence coverage so a category limit does not crowd out the receipt rule. Do not infer domestic/international from region alone; travel type is part of the retrieval question and structured applicability check.

Add `ModelTask.EXPENSE_POLICY_RULE` to the existing routing and evidence-only prompt. The gateway returns a Pydantic `PolicyRuleSet` with typed amount/receipt/prohibition/review rules, Decimal thresholds, applicability fields, and exact source chunk IDs. It cannot return the final decision. Validate each rule source against selected reranked IDs and the authoritative `validate_citations` lookup. Require the relevant numeric amount and currency to be supported by cited stored text, rejecting mismatches. Malformed, conflicting, or incomplete critical rules abstain or surface the existing typed model error. This is deliberately narrower than arbitrary free-form condition execution.

### 5. Deterministic decision and confidence

`rules/expense_rules.py` accepts validated rules, expense Decimal, and verified citation coverage. It first checks applicability, prohibition, mandatory receipt (strictly greater than the evidenced INR 500 threshold), then standard amount/unit and exception permission. A missing required receipt is NON_COMPLIANT under POL-005's mandatory requirement; a supported above-limit expense becomes NEEDS_REVIEW, not approved. Without amount-limit evidence or with incompatible unit, currency, or travel type, return INSUFFICIENT_INFORMATION. Confidence is an application-computed bounded score based on critical rule and citation coverage, not provider self-confidence; incomplete/conflicting evidence overrides score. Policy limits never come from hardcoded business constants. Explanation is deterministic from the decision and verified facts.

### 6. API, UI, observability, and errors

The thin router maps validation to 422, idempotency conflict to 409, unavailable model/retrieval/storage to controlled 503, and no usable policy evidence to an INSUFFICIENT_INFORMATION result. It propagates or creates request IDs and accepts `Idempotency-Key`. The service/repository boundary owns persistence; graph nodes call the existing RAG/Gateway interfaces. React adds an expense form and decision view alongside Q&A, with Decimal transmitted as a string, citations reused, clarification fields shown, and distinct decision states. Logs record IDs, counts/ranks, policy source IDs, model usage, rule types, confidence components, and final status; no key, full policy body, or unnecessary submitted text.

## Design Reconciliation / Decision Required

- **FRD clarification versus strict LLD sample:** use an optional-field intake schema with strict validation of supplied values and durable same-thread clarification. Do not treat omitted fields as HTTP errors.
- **FRD illustrative float versus LLD Decimal:** use Decimal and PostgreSQL NUMERIC for money.
- **Phase 004 over-limit versus FRD combined Phase 005 graph:** persist NEEDS_REVIEW and stop; later HITL consumes it.
- **Category filter versus POL-005/POL-006:** retrieve each applicable policy category separately before fused selection.
- **Existing no-key 500 fix:** retain the two uncommitted Phase 003 route/test edits in the checkout and verify them; do not fold unrelated behavior into the Phase 004 spec.

## Risks / Trade-offs

- **External model unavailable** -> Tests inject a fake gateway; runtime reports typed 503 without fabricated assessment.
- **Structured extraction does not prove semantic entailment** -> Validate exact source IDs, stored metadata and numeric support; abstain on ambiguity.
- **Reranking can drop a critical receipt section** -> Preserve category coverage in bounded evidence selection and test it.
- **Concurrent idempotent requests** -> Unique key/hash and short transactions prevent duplicate resources; pending replays remain controlled.
- **Clarification state and business truth can diverge** -> Persist and check expense status/version before resume; reconstruct from authoritative record when needed.

## Migration Plan

1. Validate the OpenSpec change, add business/checkpoint schema migration and repository models, then apply to the local PostgreSQL head.
2. Add schemas, graph/gateway/rules/service/API with fake-based tests, preserving Phase 003 Q&A behavior.
3. Add the React form/result view and golden cases, run targeted/full backend, live migration/retrieval and frontend build checks.
4. Rollback disables the Phase 004 route/UI; the new tables can be downgraded only after preserving any business records. RAG and Phase 003 schema stay unchanged.
