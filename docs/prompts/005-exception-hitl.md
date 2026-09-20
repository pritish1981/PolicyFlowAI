You are acting as a Principal AI Engineer and Senior Python/React developer implementing the next OpenSpec change for the PolicyFlow AI project.

PROJECT
-------
Project name:
PolicyFlow AI — Enterprise Expense Compliance & Exception Agent

Repository root:
D:\git-repo\PolicyFlow-AI

Current OpenSpec change:
005-exception-hitl

Source-of-truth documents:
- docs/requirements/PolicyFlow_AI_FRD_v1.0.docx
- docs/architecture/PolicyFlow_AI_HLD_v1.0.docx
- docs/architecture/PolicyFlow_AI_LLD_v1.0.docx
- openspec/project.md
- existing specifications under openspec/specs/
- completed OpenSpec changes:
  - 001-platform-foundation
  - 002-policy-ingestion-and-hybrid-rag
  - 003-policy-qa
  - 004-expense-compliance-assessment
- current repository implementation

============================================================
0. IMPORTANT WORKING RULES
============================================================

Before modifying code:

1. Inspect the full repository.
2. Read current OpenSpec project conventions.
3. Inspect:
   - openspec/specs/exception-review/
   - openspec/specs/expense-compliance/
   - openspec/specs/model-governance/
4. Inspect completed changes:
   - openspec/changes/001-platform-foundation/
   - openspec/changes/002-policy-ingestion-and-hybrid-rag/
   - openspec/changes/003-policy-qa/
   - openspec/changes/004-expense-compliance-assessment/
5. Inspect the implementation under:
   - backend/app/api/
   - backend/app/services/
   - backend/app/graph/
   - backend/app/gateway/
   - backend/app/schemas/
   - backend/app/models/
   - backend/app/repositories/
   - backend/app/rules/
   - backend/app/observability/
   - frontend/src/
   - tests/
6. Reuse all stable functionality from phases 001-004.
7. Do not duplicate expense decision logic.
8. Do not duplicate policy retrieval/RAG.
9. Do not create another graph if the existing LangGraph can be extended cleanly.
10. Do not implement Phase 006 Model Gateway hardening beyond the minimum needed for exception summaries.
11. Do not implement Phase 007 evaluation/observability beyond basic hooks already used in the project.
12. Do not implement Phase 008 AWS deployment.
13. Do not skip OpenSpec artifacts.
14. Stop after Phase 005 is complete.

Before coding, provide a short implementation plan based on the actual repository contents you find.

============================================================
1. PHASE 005 OBJECTIVE
============================================================

Implement the complete human-in-the-loop exception review flow for expenses whose Phase 004 deterministic decision is:

NEEDS_REVIEW

The required end-to-end flow is:

Expense Assessment
    ->
decision = NEEDS_REVIEW
    ->
employee submits exception justification
    ->
persist exception request
    ->
calculate deterministic variance/context
    ->
generate evidence-grounded exception summary
    ->
LangGraph enters human_review
    ->
LangGraph interrupt()
    ->
persist checkpoint in PostgreSQL
    ->
reviewer sees pending case
    ->
reviewer selects:
    APPROVE
    REJECT
    REQUEST_MORE_INFORMATION
    ->
persist authoritative reviewer action
    ->
resume LangGraph using same thread_id
    ->
finalize expense/exception state
    ->
append audit event
    ->
return final result to employee

CORE PRINCIPLE:

AI may summarize the case and evidence.

AI must NOT make the authoritative exception approval decision.

The human reviewer owns the final exception decision.

============================================================
2. OPENSPEC WORKFLOW
============================================================

Inspect:

openspec/changes/005-exception-hitl/

If incomplete, create/update:

openspec/changes/005-exception-hitl/
    proposal.md
    design.md
    tasks.md
    specs/
        exception-review/
            spec.md

Follow the exact OpenSpec style already used by phases 001-004.

Proposal must describe:

- why exception review is required;
- what capability Phase 005 introduces;
- dependency on Phase 004 NEEDS_REVIEW assessments;
- LangGraph interrupt/resume behavior;
- business persistence vs checkpoint persistence;
- reviewer workflow;
- frontend impact;
- auditability;
- explicit exclusions.

Design must cover:

- API contracts;
- exception request persistence;
- review persistence;
- LangGraph interrupt;
- PostgreSQL checkpointer;
- stable thread_id;
- reviewer queue;
- reviewer detail view;
- approve/reject/request-more-information;
- resume semantics;
- idempotent finalization;
- transaction boundaries;
- AI-generated non-authoritative review summary;
- audit events;
- error handling;
- tests.

Tasks must be checkbox-based and implementation-oriented.

Before coding:
- validate OpenSpec using locally supported commands;
- fix any validation errors;
- report the validation result;
- only then implement.

============================================================
3. STRICT PHASE 005 SCOPE
============================================================

IMPLEMENT:

A. exception request schema
B. exception persistence
C. review persistence
D. exception justification API
E. pending review API
F. review detail API if needed
G. review decision API
H. LangGraph collect_exception node
I. LangGraph human_review node
J. LangGraph interrupt()
K. PostgreSQL checkpoint integration
L. same-thread resume
M. deterministic variance calculation
N. evidence-grounded review summary
O. Model Gateway task for exception summary
P. reviewer actions:
   - APPROVE
   - REJECT
   - REQUEST_MORE_INFORMATION
Q. transactional finalization
R. duplicate review protection
S. audit events
T. employee exception UI
U. reviewer queue UI
V. reviewer detail UI
W. review decision UI
X. unit/integration/graph tests
Y. OpenSpec completion

DO NOT IMPLEMENT:

- autonomous exception approval;
- payroll/reimbursement settlement;
- enterprise SSO;
- advanced RBAC beyond current demo role abstraction;
- notification/email integrations;
- OCR;
- fraud detection;
- Ragas/DeepEval expansion;
- AWS deployment;
- major Model Gateway redesign;
- multi-agent orchestration.

============================================================
4. EXISTING PHASE 004 PRECONDITION
============================================================

Phase 005 should only accept an expense for exception review when:

assessment.decision == NEEDS_REVIEW

Do NOT permit arbitrary COMPLIANT or NON_COMPLIANT expenses to enter exception review unless the source-of-truth specs explicitly allow it.

Expected prior state:

expense exists
assessment exists
decision = NEEDS_REVIEW
policy evidence exists
citations are valid
policy_limit may exist
amount is known

Example:

expense amount = INR 9500
policy limit = INR 7000
decision = NEEDS_REVIEW

Phase 005 then owns:

justification
exception request
review queue
human decision
resume
finalization

============================================================
5. BUSINESS DATA MODEL
============================================================

Inspect current models/migrations first.

Expected logical tables:

app.exception_request

Suggested columns:

id UUID PK
expense_id UUID FK
assessment_id UUID FK
justification TEXT
variance_amount NUMERIC(12,2)
status
created_at
updated_at if used

Suggested status values:

PENDING_REVIEW
MORE_INFORMATION_REQUIRED
APPROVED
REJECTED

Use existing enums/status conventions if already defined.

Expected review table:

app.review

Suggested columns:

id UUID PK
exception_id UUID FK
reviewer_id
decision
comments
reviewed_at

Supported decisions:

APPROVE
REJECT
REQUEST_MORE_INFORMATION

Do not create duplicate tables if they already exist.

============================================================
6. BUSINESS STATE VS CHECKPOINT STATE
============================================================

Preserve the architectural separation:

BUSINESS POSTGRESQL:
- expense
- assessment
- exception_request
- review
- audit events

LANGGRAPH CHECKPOINT POSTGRESQL:
- graph execution state
- thread continuation state
- interrupt state

Important:

Checkpoint data is NOT authoritative business truth.

Final review decisions must be written transactionally to business tables.

============================================================
7. THREAD AND REQUEST IDENTIFIERS
============================================================

Preserve:

thread_id
- stable across clarification and HITL turns;
- identifies the workflow instance.

request_id
- identifies a specific HTTP/API call.

exception_id
- identifies the authoritative exception business record.

expense_id
- identifies the expense business record.

review_id
- identifies reviewer action.

The review resume operation must use the same thread_id that entered human_review.

Do not generate a new workflow thread for the reviewer decision.

============================================================
8. LANGGRAPH STATE
============================================================

Extend/reuse current graph state.

Relevant fields:

thread_id
request_id
scenario

expense_id
expense

policy_rule
citations

decision
confidence
explanation

exception_id
exception_justification

variance_amount

review_summary

reviewer_decision
reviewer_comments
reviewer_id

requires_human

model_usage
errors

Prefer IDs and compact state.

Do not persist large policy documents in the checkpoint.

============================================================
9. LANGGRAPH HITL FLOW
============================================================

Extend the existing expense workflow.

Expected flow:

evaluate_expense
    ->
decision == NEEDS_REVIEW
    ->
collect_exception
    ->
human_review
    ->
interrupt(...)
    ->
WAIT
    ->
resume with reviewer payload
    ->
finalize_decision
    ->
audit_event
    ->
END

For Phase 005, implement this branch cleanly.

Do not change the happy paths:

COMPLIANT
NON_COMPLIANT
INSUFFICIENT_INFORMATION

unless needed to connect the graph cleanly.

============================================================
10. COLLECT_EXCEPTION NODE
============================================================

Implement/reuse:

backend/app/graph/nodes/collect_exception.py

Responsibilities:

- validate that expense is eligible for exception;
- validate employee justification;
- load current assessment;
- calculate deterministic variance where applicable;
- create or reference exception record;
- prepare review context;
- optionally invoke exception-summary generation through Model Gateway;
- set requires_human = true;
- route to human_review.

Do not make a final business decision here.

============================================================
11. DETERMINISTIC VARIANCE
============================================================

Where policy limit exists:

variance_amount =
expense.amount - policy_limit

Use Decimal.

Example:

expense = 9500
policy_limit = 7000

variance =
2500

Do not ask the LLM to calculate variance.

If no numeric limit exists:
variance may be null.

============================================================
12. EXCEPTION SUMMARY
============================================================

Add or reuse a Model Gateway task:

EXCEPTION_REVIEW_SUMMARY

Input:

- expense details;
- applicable PolicyRule;
- deterministic variance;
- employee justification;
- verified citations.

Output should be strictly non-authoritative.

Suggested schema:

class ExceptionReviewSummary(BaseModel):
    summary: str
    key_facts: list[str]
    risk_or_attention_points: list[str]
    citation_chunk_ids: list[UUID]

Do NOT include:

recommended_decision = APPROVE

as an authoritative field.

If a recommendation-like field already exists, it must be explicitly non-binding.

Preferred prompt rules:

1. Use only supplied expense data and verified policy evidence.
2. Do not invent policy rules.
3. Do not invent justification facts.
4. Do not approve or reject.
5. Summarize the case neutrally.
6. Highlight relevant policy variance and missing information.
7. Cite only supplied chunk IDs.

============================================================
13. HUMAN_REVIEW NODE
============================================================

Implement/reuse:

backend/app/graph/nodes/human_review.py

The node should invoke LangGraph interrupt().

Suggested interrupt payload:

{
  "exception_id": "...",
  "expense_id": "...",
  "expense_summary": {...},
  "policy_rule": {...},
  "variance_amount": "...",
  "justification": "...",
  "review_summary": "...",
  "citations": [...]
}

The interrupt payload should contain enough information for the reviewer UI.

Do not include secrets or unnecessary internal state.

============================================================
14. CHECKPOINTER
============================================================

Use PostgreSQL LangGraph checkpointer.

Inspect existing implementation first.

Expected behavior:

graph invoked with config:

{
  "configurable": {
    "thread_id": "<stable-thread-id>"
  }
}

When human_review calls interrupt():
- state is persisted;
- API returns a pending-review result;
- process/container may safely stop.

When reviewer responds:
- reload checkpoint using same thread_id;
- resume graph.

Do not use in-memory-only checkpointing for the real integration path.

Tests may use an in-memory checkpointer when appropriate.

============================================================
15. EXCEPTION REQUEST API
============================================================

Implement/update:

POST /api/v1/expenses/{expense_id}/exceptions

Suggested request:

{
  "justification": "Conference hotel rates were higher because approved hotels were unavailable."
}

Validation:

- justification required;
- minimum sensible length;
- maximum safe length;
- expense exists;
- assessment exists;
- assessment decision == NEEDS_REVIEW;
- no already-finalized exception;
- no duplicate uncontrolled exception creation.

Expected response:

{
  "exception_id": "...",
  "expense_id": "...",
  "thread_id": "...",
  "status": "PENDING_REVIEW",
  "variance_amount": "2500.00",
  "next_action": "WAIT_FOR_REVIEW"
}

Use existing response conventions if present.

============================================================
16. PENDING REVIEW API
============================================================

Implement/update:

GET /api/v1/reviews/pending

Return pending exception cases.

Suggested response fields:

exception_id
expense_id
expense_type
amount
currency
policy_limit
variance_amount
justification
created_at

Do not expose unnecessary internals.

Apply current demo REVIEWER role check if available.

============================================================
17. REVIEW DETAIL API
============================================================

If necessary for the frontend, implement:

GET /api/v1/reviews/{exception_id}

Return:

- expense details;
- assessment;
- applicable PolicyRule;
- citations;
- variance;
- justification;
- review summary;
- current status.

If existing APIs already provide equivalent data:
reuse them.

============================================================
18. REVIEW DECISION API
============================================================

Implement/update:

POST /api/v1/reviews/{exception_id}/decision

Request:

{
  "decision": "APPROVE",
  "comments": "Business justification accepted.",
  "reviewer_id": "reviewer-demo"
}

or reviewer_id derived from current auth/demo context.

Allowed decisions:

APPROVE
REJECT
REQUEST_MORE_INFORMATION

Use Pydantic Literal/enum validation.

============================================================
19. REVIEW RESUME PAYLOAD
============================================================

Use/reuse:

class ReviewResumePayload(BaseModel):
    exception_id: UUID
    reviewer_id: str
    decision: Literal[
        "APPROVE",
        "REJECT",
        "REQUEST_MORE_INFORMATION"
    ]
    comments: str

Resume:

graph.invoke(
    Command(
        resume=ReviewResumePayload(...)
    ),
    config={
        "configurable": {
            "thread_id": thread_id
        }
    }
)

Adapt to actual LangGraph version/API installed in the repository.

Do not blindly copy API syntax if the installed version differs.

============================================================
20. APPROVE FLOW
============================================================

When reviewer chooses APPROVE:

1. lock/load exception;
2. verify current state is PENDING_REVIEW;
3. persist review record;
4. update exception status = APPROVED;
5. update expense/final status according to current model;
6. append audit event;
7. resume graph;
8. graph finalizes;
9. return final approved outcome.

AI does not own this decision.

============================================================
21. REJECT FLOW
============================================================

When reviewer chooses REJECT:

1. validate pending state;
2. persist review;
3. exception status = REJECTED;
4. update expense status accordingly;
5. append audit event;
6. resume graph;
7. return final rejected outcome.

Do not reinterpret or override reviewer choice with the model.

============================================================
22. REQUEST_MORE_INFORMATION FLOW
============================================================

When reviewer chooses REQUEST_MORE_INFORMATION:

Do not finalize as approved/rejected.

Expected behavior:

exception status =
MORE_INFORMATION_REQUIRED

Return to employee:

next_action =
PROVIDE_MORE_INFORMATION

The employee should be able to provide additional information/clarification.

Keep the workflow resumable.

Do not over-engineer multiple reviewer rounds unless the existing design already supports them.

Minimum acceptable Phase 005 behavior:

Reviewer requests more information
    ->
status updated
    ->
employee provides additional information
    ->
case can return to PENDING_REVIEW
    ->
reviewer may decide again

If this requires an endpoint, use the smallest consistent design.

============================================================
23. FINALIZATION TRANSACTION
============================================================

Reviewer finalization MUST be transactional.

Expected transaction:

BEGIN

lock exception row

verify:
status == PENDING_REVIEW

insert review

update exception

update expense/final state

append audit event

COMMIT

If already finalized:

return HTTP 409

Do not allow double approval or double rejection.

============================================================
24. DUPLICATE ACTION PROTECTION
============================================================

Two reviewer requests may arrive concurrently.

Protect using one or more:

- SELECT ... FOR UPDATE
- unique constraint
- status check inside transaction
- idempotency key if already used by the project

Desired behavior:

first valid final decision:
success

second conflicting/final duplicate:
409 Conflict

Do not rely only on frontend button disabling.

============================================================
25. BUSINESS FINALIZATION AND GRAPH RESUME
============================================================

Important ordering:

The authoritative review/business state must be committed safely.

Then graph resume/finalization must produce a consistent final response.

If the exact existing design handles graph resume before final commit, inspect and preserve correct transactional guarantees.

Never use checkpoint state as a replacement for business transaction integrity.

============================================================
26. FRONTEND EMPLOYEE FLOW
============================================================

Implement/reuse components such as:

frontend/src/components/
    ExceptionForm.tsx

frontend/src/pages/
    ExpenseAssessmentPage.tsx

If Phase 004 returns:

decision = NEEDS_REVIEW

show:

"Submit Exception Justification"

Form:

Justification textarea
Submit button
validation
loading state
error state

After submission:

show:

Exception submitted
Status: Pending Review

Do not show fake reviewer decisions.

============================================================
27. REVIEWER UI
============================================================

Implement/reuse:

frontend/src/pages/
    ReviewerPage.tsx

frontend/src/components/
    ReviewPanel.tsx

Suggested UI:

Pending Reviews list

Select case

Show:

Expense:
- type
- amount
- location
- purpose
- receipt

Policy:
- policy code
- policy limit
- section
- citations

Exception:
- variance
- justification

AI Summary:
- neutral case summary

Actions:

APPROVE
REJECT
REQUEST MORE INFORMATION

Comment field required.

Keep interface simple.

============================================================
28. REVIEWER AUTH / ROLE
============================================================

Use the current POC role mechanism.

Expected roles may include:

EMPLOYEE
REVIEWER
ADMIN

Do not implement enterprise SSO in Phase 005.

Reviewer APIs should require REVIEWER where current infrastructure allows.

Keep role handling replaceable by enterprise OIDC later.

============================================================
29. AUDIT EVENTS
============================================================

Record meaningful events.

Suggested event types:

EXCEPTION_CREATED
EXCEPTION_SUBMITTED
HUMAN_REVIEW_INTERRUPTED
REVIEW_APPROVED
REVIEW_REJECTED
REVIEW_MORE_INFO_REQUESTED
WORKFLOW_RESUMED
EXCEPTION_FINALIZED

Capture:

event_id
thread_id
request_id
expense_id
exception_id
reviewer_id where applicable
event_type
timestamp

Also preserve relevant model metadata for the generated review summary if available.

Do not log secrets.

============================================================
30. OBSERVABILITY
============================================================

Capture:

request_id
thread_id
expense_id
exception_id

graph:
node_name
interrupt event
resume event
duration

model:
task=EXCEPTION_REVIEW_SUMMARY
provider
model
prompt_version
token usage
latency

business:
variance
review status
review decision

quality:
valid citation count

Do not put full justification text into external telemetry unless already explicitly allowed.

============================================================
31. ERROR HANDLING
============================================================

Expected behavior:

expense not found
-> 404

assessment not found
-> 404 / domain-specific error

expense not eligible for exception
-> 409

exception already exists
-> 409 unless current design allows safe reuse

exception already finalized
-> 409

invalid reviewer decision
-> 422

thread/checkpoint not found
-> 404 or workflow-state error

invalid checkpoint state
-> 409

PostgreSQL unavailable
-> fail request

model summary unavailable
-> do NOT block reviewer action if summary is optional
   OR use documented safe behavior

AI summary failure must never cause automatic approval/rejection.

============================================================
32. MODEL FAILURE DURING EXCEPTION SUMMARY
============================================================

The exception review summary is an assistant feature, not business authority.

Therefore:

If Model Gateway summary generation fails:

- retain expense;
- retain exception request;
- retain policy evidence;
- allow human review to proceed if sufficient deterministic data exists;
- mark summary unavailable;
- emit telemetry.

Do not block a legitimate human reviewer unnecessarily just because the summary model failed.

Follow source-of-truth specs if they define stricter behavior.

============================================================
33. CITATIONS IN REVIEW FLOW
============================================================

Reuse verified citations from Phase 004.

Do not rerun citation validation unnecessarily if already authoritative and unchanged.

However, before presenting a material policy source to reviewer:

ensure citation metadata is still valid and available.

Reviewer must see:

policy_code
version
section
excerpt

Server-side excerpts only.

============================================================
34. TESTING STRATEGY
============================================================

Add comprehensive tests.

UNIT TESTS

A. Exception eligibility:
- NEEDS_REVIEW eligible
- COMPLIANT not eligible
- NON_COMPLIANT not eligible
- already finalized not eligible

B. Justification validation:
- valid
- blank
- too short
- too long

C. Variance:
9500 - 7000 = 2500
Decimal accuracy
null when no limit

D. Review schema:
APPROVE valid
REJECT valid
REQUEST_MORE_INFORMATION valid
invalid decision rejected

E. Review-summary schema:
valid summary
invalid citation IDs
no authoritative decision field

F. State transitions:
PENDING_REVIEW -> APPROVED
PENDING_REVIEW -> REJECTED
PENDING_REVIEW -> MORE_INFORMATION_REQUIRED
finalized -> cannot decide again

GRAPH TESTS

1.
NEEDS_REVIEW
-> collect_exception
-> human_review
-> interrupt

2.
resume APPROVE
-> finalize
-> END

3.
resume REJECT
-> finalize
-> END

4.
REQUEST_MORE_INFORMATION
-> appropriate continuation/state

5.
checkpoint survives recreation/reload where integration environment permits

SERVICE TESTS

- exception record created
- review queue contains pending item
- approve persists review
- reject persists review
- duplicate finalization returns conflict
- summary model failure does not corrupt business state

INTEGRATION TESTS

POST exception
GET pending reviews
POST APPROVE decision
verify DB state

Repeat for REJECT.

Test REQUEST_MORE_INFORMATION path.

No live OpenAI dependency required in CI.

============================================================
35. END-TO-END DEMO CASE
============================================================

Use this example:

Phase 004 result:

Expense:
HOTEL
INR 9500
DOMESTIC
Bengaluru
Client conference
Receipt = true

Policy:
POL-002
Domestic hotel limit = INR 7000

Decision:
NEEDS_REVIEW

Phase 005:

Employee justification:

"Approved hotels were unavailable near the conference venue, so the available hotel rate was INR 9500."

System:

variance =
9500 - 7000 =
2500

creates exception

generates neutral summary

interrupts graph

reviewer sees:

Expense amount: INR 9500
Policy limit: INR 7000
Variance: INR 2500
Justification
POL-002 citation
AI summary

Reviewer:

APPROVE

System:

persist review
update exception
append audit
resume graph
finalize
return final approved result

Repeat demo mentally for:

REJECT

and:

REQUEST_MORE_INFORMATION

============================================================
36. DATABASE MIGRATIONS
============================================================

Inspect current Alembic migrations before creating anything.

Do not recreate:
- expense table
- assessment table
- RAG tables

Only add:

exception_request
review
or missing required columns/constraints

if they are not already implemented.

Expected constraints:

- FK exception -> expense
- FK exception -> assessment
- FK review -> exception
- unique/final-review protection as appropriate
- status constraints
- timestamps

Run:

python -m alembic current
python -m alembic upgrade head

Verify migration head.

============================================================
37. ARCHITECTURAL CONSTRAINTS
============================================================

Preserve:

React
 ->
FastAPI
 ->
Service
 ->
LangGraph
 ->
collect_exception
 ->
human_review
 ->
interrupt
 ->
PostgreSQL checkpoint
 ->
Human Reviewer
 ->
resume
 ->
finalize_decision
 ->
business persistence
 ->
audit

Business authority:

Human reviewer

AI responsibility:

summarization/context support only

LangGraph responsibility:

workflow state/orchestration

PostgreSQL business DB:

authoritative final state

============================================================
38. IMPORTANT SAFETY / GOVERNANCE BOUNDARY
============================================================

This must never occur:

LLM says:
"APPROVE"

and system automatically approves.

Correct flow:

LLM:
"Here is a neutral summary of the case."

Human reviewer:
APPROVE / REJECT / REQUEST_MORE_INFORMATION

System:
persists human decision.

============================================================
39. IMPLEMENTATION ORDER
============================================================

Implement incrementally:

Step 1
Inspect completed Phase 004 implementation.

Step 2
Inspect/create OpenSpec 005 artifacts.

Step 3
Validate OpenSpec.

Step 4
Inspect existing exception/review models.

Step 5
Add/verify Alembic migration.

Step 6
Implement exception/review Pydantic schemas.

Step 7
Implement exception/review repository methods.

Step 8
Implement deterministic variance logic.

Step 9
Add EXCEPTION_REVIEW_SUMMARY Model Gateway task.

Step 10
Implement exception summary prompt/schema.

Step 11
Implement collect_exception node.

Step 12
Implement human_review interrupt node.

Step 13
Configure/verify PostgreSQL checkpointer.

Step 14
Implement exception submission service/API.

Step 15
Implement pending review service/API.

Step 16
Implement review-decision transaction.

Step 17
Implement LangGraph resume.

Step 18
Implement APPROVE finalization.

Step 19
Implement REJECT finalization.

Step 20
Implement REQUEST_MORE_INFORMATION behavior.

Step 21
Add audit events.

Step 22
Implement employee exception form.

Step 23
Implement reviewer queue.

Step 24
Implement reviewer detail/action UI.

Step 25
Add unit tests.

Step 26
Add graph/checkpoint tests.

Step 27
Add integration tests.

Step 28
Run migrations.

Step 29
Run backend tests.

Step 30
Run frontend build/tests.

Step 31
Validate OpenSpec.

Step 32
Update tasks.md accurately.

STOP.

Do not begin Phase 006.

============================================================
40. VALIDATION COMMANDS
============================================================

Use actual repository tooling.

Backend:

python -m pytest -v

or targeted:

python -m pytest backend/tests -v

Database:

python -m alembic current
python -m alembic upgrade head

Frontend:

npm run build

OpenSpec:

use the locally supported commands, such as:

openspec status
openspec validate

Do not invent unsupported flags.

If a command fails:

- show exact command;
- show exact error;
- fix if in scope;
- rerun.

============================================================
41. PHASE 005 ACCEPTANCE CRITERIA
============================================================

Phase 005 is complete only when:

[ ] OpenSpec 005 proposal/design/spec/tasks are valid

[ ] only NEEDS_REVIEW expenses enter exception flow

[ ] employee can submit exception justification

[ ] exception request is persisted

[ ] variance is calculated deterministically

[ ] AI summary is non-authoritative

[ ] human_review uses LangGraph interrupt

[ ] PostgreSQL checkpointer persists state

[ ] same thread_id resumes workflow

[ ] pending review list works

[ ] reviewer can APPROVE

[ ] reviewer can REJECT

[ ] reviewer can REQUEST_MORE_INFORMATION

[ ] final reviewer decision is persisted in business tables

[ ] duplicate finalization is prevented

[ ] review transaction is atomic

[ ] audit events are recorded

[ ] AI cannot autonomously approve

[ ] employee UI supports exception submission

[ ] reviewer UI supports pending review and decision

[ ] graph tests pass

[ ] API integration tests pass

[ ] migrations are current

[ ] frontend build passes

[ ] no live model dependency is required in CI

[ ] no secrets are committed

[ ] OpenSpec tasks match actual state

============================================================
42. FINAL REPORT
============================================================

When implementation is complete, provide:

1. OpenSpec files created/modified
2. database migration changes
3. models created/modified
4. schemas created/modified
5. repository changes
6. service changes
7. graph/state/node changes
8. checkpointer changes
9. Model Gateway changes
10. APIs added/changed
11. frontend changes
12. audit/observability changes
13. tests added
14. commands executed
15. migration result
16. backend test results
17. frontend build result
18. OpenSpec validation result
19. known limitations
20. explicitly deferred Phase 006 items
21. end-to-end HITL flow summary

Do not merely say:
"Phase 005 implemented."

Show actual implementation and validation evidence.

STOP after Phase 005.
Do not automatically proceed to Phase 006.

============================================================
43. FILES CREATED OR UPDATED DURING PHASE 005
============================================================

Source of truth: Phase 005 commit `7385200` (`feat: complete Phase 005 exception HITL workflow`).

Files created (14):

- `backend/alembic/versions/20260920_0004_exception_hitl.py`
- `backend/tests/test_exception_hitl.py`
- `backend/tests/test_exception_workflow_integration.py`
- `frontend/src/api/reviewApi.ts`
- `frontend/src/pages/ExpensePage.test.tsx`
- `frontend/src/pages/ReviewerPage.test.tsx`
- `frontend/src/pages/ReviewerPage.tsx`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/.openspec.yaml`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/design.md`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/proposal.md`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/specs/exception-review/spec.md`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/specs/expense-compliance/spec.md`
- `openspec/changes/archive/2026-09-20-005-exception-hitl/tasks.md`
- `openspec/specs/exception-review/spec.md`

Files updated (30):

- `README.md`
- `backend/app/api/dependencies.py`
- `backend/app/api/routes/expenses.py`
- `backend/app/api/routes/reviews.py`
- `backend/app/core/exceptions.py`
- `backend/app/gateway/prompts.py`
- `backend/app/gateway/routing.py`
- `backend/app/graph/expense_graph.py`
- `backend/app/graph/nodes/collect_exception.py`
- `backend/app/graph/nodes/finalize_decision.py`
- `backend/app/graph/nodes/human_review.py`
- `backend/app/graph/state.py`
- `backend/app/main.py`
- `backend/app/models/audit_event.py`
- `backend/app/models/exception_request.py`
- `backend/app/models/review.py`
- `backend/app/repositories/review_repository.py`
- `backend/app/schemas/expense.py`
- `backend/app/schemas/review.py`
- `backend/app/services/exception_service.py`
- `backend/app/services/expense_service.py`
- `backend/tests/test_policy_rag_integration.py`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/api/types.ts`
- `frontend/src/pages/ExpensePage.tsx`
- `frontend/tsconfig.tsbuildinfo`
- `openspec/specs/expense-compliance/spec.md`
