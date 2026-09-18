You are acting as a Principal AI Engineer and Senior Python/React developer implementing the next OpenSpec change for the PolicyFlow AI project.

PROJECT
-------
Project name:
PolicyFlow AI — Enterprise Expense Compliance & Exception Agent

Repository root:
D:\git-repo\PolicyFlow-AI

Current OpenSpec change:
004-expense-compliance-assessment

Source-of-truth documents:
- docs/requirements/PolicyFlow_AI_FRD_v1.0.docx
- docs/architecture/PolicyFlow_AI_HLD_v1.0.docx
- docs/architecture/PolicyFlow_AI_LLD_v1.0.docx
- openspec/project.md
- existing specifications under openspec/specs/
- completed changes:
  - 001-platform-foundation
  - 002-policy-ingestion-and-hybrid-rag
  - 003-policy-qa
- current repository implementation

============================================================
0. BEFORE WRITING CODE
============================================================

Before modifying code:

1. Inspect the entire current repository.
2. Read the OpenSpec project configuration and conventions.
3. Inspect completed OpenSpec changes:
   - openspec/changes/001-platform-foundation/
   - openspec/changes/002-policy-ingestion-and-hybrid-rag/
   - openspec/changes/003-policy-qa/
4. Inspect:
   - openspec/specs/expense-compliance/
   - openspec/specs/policy-rag/
   - openspec/specs/model-governance/
5. Inspect existing backend implementation under:
   - backend/app/api/
   - backend/app/services/
   - backend/app/graph/
   - backend/app/rag/
   - backend/app/gateway/
   - backend/app/schemas/
   - backend/app/models/
   - backend/app/repositories/
   - backend/app/rules/
   - backend/app/observability/
6. Inspect current frontend:
   - frontend/src/api/
   - frontend/src/components/
   - frontend/src/pages/
   - frontend/src/types/
7. Inspect tests and existing fixtures.
8. Reuse all working Phase 001–003 functionality.
9. Do not rewrite working Policy Q&A/RAG/Model Gateway components unnecessarily.
10. Do not implement Phase 005 HITL exception review yet.
11. Do not skip OpenSpec proposal/design/spec/tasks.

First provide a short implementation plan based on the code you actually find.

============================================================
1. PHASE 004 OBJECTIVE
============================================================

Implement the complete structured Expense Compliance Assessment use case.

Example request:

Expense type: HOTEL
Amount: INR 9500
Location: Bengaluru
Travel type: DOMESTIC
Purpose: Client meeting
Receipt available: true

Expected flow:

React Expense Form
    ->
POST /api/v1/expenses
    ->
FastAPI / Pydantic validation
    ->
create authoritative expense business record
    ->
ExpenseService
    ->
LangGraph expense_assessment path
    ->
detect missing mandatory fields
    ->
if missing:
    targeted clarification response
else:
    deterministic metadata filters
    ->
reuse Phase 002/003 Hybrid RAG
        PostgreSQL FTS
        +
        pgvector semantic search
        ->
        RRF
        ->
        reranking
        ->
        top policy evidence
    ->
Model Gateway
    ->
structured PolicyRule extraction
    ->
deterministic business-rule evaluation
    ->
citation validation
    ->
confidence/evidence evaluation
    ->
persist assessment
    ->
return:

COMPLIANT
NON_COMPLIANT
NEEDS_REVIEW
or
INSUFFICIENT_INFORMATION

IMPORTANT ARCHITECTURAL PRINCIPLE:

The LLM interprets policy evidence.
Deterministic Python code makes the compliance decision.

The LLM must NEVER directly decide whether the expense is compliant.

============================================================
2. OPENSPEC WORKFLOW
============================================================

Inspect:

openspec/changes/004-expense-compliance-assessment/

If incomplete, create/update:

openspec/changes/004-expense-compliance-assessment/
    proposal.md
    design.md
    tasks.md
    specs/
        expense-compliance/
            spec.md

Follow the exact OpenSpec style already used by changes 001–003.

Proposal must define:
- business problem;
- new capability;
- dependency on Phase 002 Hybrid RAG;
- dependency on Phase 003 Model Gateway / citations where reusable;
- API impact;
- graph impact;
- persistence impact;
- frontend impact;
- testing impact;
- explicit out-of-scope items.

Design must cover:
- request/response contracts;
- expense persistence;
- LangGraph assessment path;
- clarification path;
- metadata filtering;
- hybrid RAG reuse;
- PolicyRule extraction;
- deterministic decision algorithm;
- receipt checks;
- amount checks;
- citation validation;
- confidence/evidence handling;
- transaction boundaries;
- idempotency;
- frontend behavior;
- observability;
- testing.

Tasks must be implementation-oriented and checkbox-based.

Before implementation:
- validate OpenSpec using available local commands;
- fix errors;
- report validation status;
- then proceed.

============================================================
3. STRICT PHASE 004 SCOPE
============================================================

IMPLEMENT:

A. Structured expense request/response schemas
B. POST /api/v1/expenses
C. authoritative expense persistence
D. assessment persistence
E. ExpenseService
F. LangGraph expense_assessment path
G. mandatory-field detection
H. clarification-needed response contract
I. reuse hybrid retrieval
J. deterministic metadata filters
K. structured PolicyRule extraction
L. Model Gateway EXPENSE_POLICY_RULE task
M. deterministic expense-rule engine
N. receipt/document checks
O. amount threshold checks
P. policy citation validation
Q. confidence/evidence evaluation
R. safe abstention
S. assessment result persistence
T. React expense form
U. React assessment result display
V. backend tests
W. frontend validation/build
X. OpenSpec task completion

DO NOT IMPLEMENT:

- exception justification submission;
- reviewer queue;
- reviewer approve/reject action;
- LangGraph human_review interrupt;
- resume after reviewer decision;
- reviewer UI;
- exception finalization;
- AWS deployment;
- full LangWatch dashboards;
- full Ragas/DeepEval suite;
- OCR receipt extraction;
- fraud detection;
- payment/reimbursement processing;
- autonomous exception approval.

Those belong to later phases.

============================================================
4. API CONTRACT
============================================================

Implement:

POST /api/v1/expenses

Use existing route layout if different, but preserve architectural boundaries.

Suggested request:

{
  "expense_type": "HOTEL",
  "amount": "9500.00",
  "currency": "INR",
  "location": "Bengaluru",
  "travel_type": "DOMESTIC",
  "purpose": "Client meeting",
  "receipt_available": true
}

Use Decimal for money.

Suggested Pydantic model:

class ExpenseCreate(BaseModel):
    expense_type: Literal["HOTEL", "MEAL", "TAXI"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = "INR"
    location: str
    travel_type: Literal["DOMESTIC", "INTERNATIONAL"]
    purpose: str
    receipt_available: bool

Response:

class ExpenseAssessmentResponse(BaseModel):
    expense_id: UUID
    thread_id: str
    decision: Literal[
        "COMPLIANT",
        "NON_COMPLIANT",
        "NEEDS_REVIEW",
        "INSUFFICIENT_INFORMATION"
    ]
    policy_limit: Decimal | None
    confidence: float
    explanation: str
    citations: list[Citation]
    next_action: str | None

If missing information is supported via the same endpoint, return a controlled response such as:

{
  "expense_id": "...",
  "thread_id": "...",
  "decision": "INSUFFICIENT_INFORMATION",
  "missing_fields": ["purpose"],
  "next_action": "PROVIDE_CLARIFICATION"
}

Do not invent undocumented fields if an existing schema already defines a better structure.

============================================================
5. EXPENSE BUSINESS RECORD
============================================================

Persist the expense as authoritative business state.

Expected logical table:

app.expense

Fields should include, where already defined by migration/model:

id
employee_id if present
expense_type
amount NUMERIC(12,2)
currency
location
travel_type
purpose
receipt_available
status
created_at
updated_at

Important:

- PostgreSQL business state is authoritative.
- LangGraph checkpoint state must not replace the business record.
- Do not persist money as float.
- use Decimal / NUMERIC.

If app.expense already exists:
reuse it.

If not:
create the minimum Alembic migration aligned with the LLD.

Do not create duplicate tables.

============================================================
6. ASSESSMENT BUSINESS RECORD
============================================================

Persist assessment results separately.

Expected logical table:

app.assessment

Suggested fields:

id
expense_id FK
decision
policy_rule JSONB
confidence
explanation
model_name
prompt_version
created_at

Preserve:
- applicable policy rule;
- final deterministic decision;
- confidence;
- explanation;
- model metadata;
- citations or citation references if current schema supports them.

Do not rely only on graph checkpoint storage.

============================================================
7. IDEMPOTENCY
============================================================

POST /api/v1/expenses should support an Idempotency-Key if the existing design/framework already includes it.

Desired behavior:

same key + same payload
-> return same created result where feasible

same key + different payload
-> HTTP 409

Do not over-engineer a distributed idempotency platform.

Use the existing repository/database approach.

============================================================
8. LANGGRAPH STATE
============================================================

Extend the existing graph state rather than creating a competing graph.

Relevant fields:

thread_id
request_id
scenario = "expense_assessment"

expense_id
expense

missing_fields

metadata_filters

lexical_hits
vector_hits
fused_hits
reranked_hits

policy_rule
citations

decision
confidence
explanation

model_usage
errors

Do not persist entire source documents unnecessarily.

Prefer compact ID-oriented state.

============================================================
9. EXPENSE ASSESSMENT GRAPH
============================================================

Implement the Phase 004 branch:

START
  ->
validate_request
  ->
detect_missing_fields
  ->
if missing:
    request_clarification / clarification response
else:
    build_metadata_filters
      ->
    hybrid_retrieve
      ->
    fuse_results
      ->
    rerank_results
      ->
    extract_policy_rule
      ->
    evaluate_expense
      ->
    validate_citations
      ->
    evaluate_confidence
      ->
    finalize_assessment
      ->
    audit/log
      ->
    END

Do not route NEEDS_REVIEW into human_review yet.

For Phase 004:

NEEDS_REVIEW
-> persist assessment
-> return next_action indicating exception review is required
-> stop

Phase 005 will implement the exception/HITL path.

============================================================
10. MISSING-FIELD DETECTION
============================================================

Implement deterministic detection.

Required fields for current POC:

expense_type
amount
currency
location
travel_type
purpose
receipt_available

Do not ask the LLM whether required fields are missing.

If the request schema rejects missing fields at HTTP validation before the graph can handle clarification, reconcile the API contract carefully:

Preferred option:
allow optional fields in a dedicated intake schema
and let detect_missing_fields produce targeted clarification.

Alternative:
if current design intentionally requires all fields at API level,
keep 422 validation and document that clarification is deferred.

Choose based on existing repository/OpenSpec behavior.

Do not silently invent a conflicting contract.

============================================================
11. METADATA FILTER CONSTRUCTION
============================================================

Reuse Phase 003 deterministic metadata filter logic.

Always enforce:

status = ACTIVE

Also enforce validity dates when available:

effective_date <= assessment_date

and:

expiry_date is null
OR
assessment_date < expiry_date

Map expense context to retrieval filters where appropriate:

HOTEL
-> HOTEL category

MEAL
-> MEAL category

TAXI
-> GROUND_TRANSPORTATION category

travel_type / region should only be applied when compatible with existing policy metadata.

Do not over-filter when metadata is absent.

Do not let the LLM decide active/inactive policy eligibility.

============================================================
12. REUSE PHASE 002/003 RAG PIPELINE
============================================================

DO NOT create a second retrieval implementation.

Reuse:

- lexical retriever
- vector retriever
- hybrid retriever
- RRF
- reranker
- citation validator

Expected retrieval values:

lexical top N = 20
vector top N = 20
RRF k = 60
fused candidates = 10–20
final evidence = top 3–5

Preserve:

chunk_id
policy_code
version
section
content
lexical_rank
vector_rank
rrf_score
rerank_score
metadata

============================================================
13. POLICY RULE STRUCTURED MODEL
============================================================

Implement/reuse:

class PolicyRule(BaseModel):
    rule_type: Literal[
        "AMOUNT_LIMIT",
        "RECEIPT_REQUIRED",
        "PROHIBITION",
        "REVIEW_REQUIRED"
    ]
    category: str
    amount_limit: Decimal | None = None
    currency: str | None = None
    condition: str | None = None
    source_chunk_ids: list[UUID]

If an existing schema already includes extra safe fields, preserve them.

Important:

- amount_limit must be Decimal;
- source_chunk_ids must reference retrieved/reranked evidence;
- no free-form unvalidated model JSON;
- no float for money.

============================================================
14. MODEL GATEWAY TASK
============================================================

Add/reuse a Model Gateway task:

EXPENSE_POLICY_RULE

All LLM calls must continue through the existing central Model Gateway.

No direct OpenAI SDK calls from:
- graph nodes;
- API;
- service;
- rule engine;
- retriever.

The task receives:

expense context
+
top reranked evidence

The model's ONLY responsibility:

extract the applicable policy rule into PolicyRule.

The model must NOT return:
COMPLIANT
NON_COMPLIANT
NEEDS_REVIEW

Those are deterministic application decisions.

============================================================
15. POLICY RULE EXTRACTION PROMPT
============================================================

Use an evidence-only prompt.

SYSTEM PRINCIPLES:

You extract structured policy rules from provided enterprise expense-policy evidence.

Rules:

1. Use only supplied evidence.
2. Never invent policy limits.
3. Never invent receipt requirements.
4. Never invent exception conditions.
5. Never decide whether the expense is compliant.
6. Return only the rule applicable to the supplied expense context.
7. source_chunk_ids must reference supplied chunk IDs exactly.
8. If evidence is insufficient or conflicting, return an explicit insufficient result or structured failure according to existing gateway conventions.
9. Do not use external knowledge.

Input:

Expense:
- type
- amount
- currency
- location
- travel_type
- purpose
- receipt_available

Evidence:
top reranked chunks with:
- chunk_id
- policy_code
- version
- section
- content

Output:
PolicyRule

============================================================
16. DETERMINISTIC DECISION ENGINE
============================================================

Implement under the existing rules module.

Suggested file if consistent with repository:

backend/app/rules/expense_rules.py

The decision algorithm MUST be deterministic.

Order:

1. Require at least one valid active policy citation/evidence source.

2. Convert monetary values to Decimal.

3. If policy explicitly prohibits the category/condition:
   -> NON_COMPLIANT

4. If mandatory receipt/document condition fails:
   -> policy-defined NON_COMPLIANT
      or NEEDS_REVIEW
   according to retrieved policy evidence/configuration.

5. If amount_limit exists
   and amount <= amount_limit
   and all other mandatory conditions pass:
   -> COMPLIANT

6. If amount_limit exists
   and amount > amount_limit
   and exception is allowed:
   -> NEEDS_REVIEW

7. If evidence is incomplete/conflicting:
   -> INSUFFICIENT_INFORMATION

8. LLM recommendation must NEVER override these rules.

The rule engine must be separately unit-testable without OpenAI.

============================================================
17. REQUIRED SYNTHETIC RULES
============================================================

Use retrieved policies as source of truth.

Expected baseline corpus includes:

Domestic hotel:
INR 7,000/night

International hotel:
INR 15,000/night

Domestic meal:
INR 1,500/day

Airport taxi:
INR 2,000/trip

Receipt:
required when individual expense > INR 500

Above standard threshold:
exception review required when permitted.

IMPORTANT:

Do not hardcode all policy thresholds directly into decision code as the primary source of truth.

Threshold values should come from structured PolicyRule extracted from verified retrieved policy evidence.

Code should implement comparison behavior, not duplicate the policy corpus.

============================================================
18. EXAMPLE HOTEL DECISIONS
============================================================

Example A:

HOTEL
amount = INR 6500
DOMESTIC
receipt_available = true

Retrieved verified rule:
limit = INR 7000

Expected:
COMPLIANT

assuming no other mandatory condition fails.

Example B:

HOTEL
amount = INR 9500
DOMESTIC
receipt_available = true

Retrieved verified rule:
limit = INR 7000
exception permitted/review required

Expected:
NEEDS_REVIEW

variance:
INR 2500

Do not yet create the reviewer workflow.

Example C:

HOTEL
amount = INR 6500
DOMESTIC
receipt_available = false

If retrieved policy establishes receipt mandatory > INR 500:

Expected:
NON_COMPLIANT or NEEDS_REVIEW

Use policy-defined behavior.

Do not invent the result if policy evidence is ambiguous.

Example D:

No valid policy evidence

Expected:
INSUFFICIENT_INFORMATION

============================================================
19. RECEIPT RULE HANDLING
============================================================

Receipt validation must be deterministic.

For a retrieved rule such as:

receipt required when amount > INR 500

code must evaluate:

amount > 500
AND receipt_available == false

Do not ask the LLM to calculate this.

The LLM may extract:

rule_type = RECEIPT_REQUIRED
condition = "amount > 500"

but application code owns the actual check.

Prefer strongly typed rule representation if current schemas support it.

Avoid unsafe free-form condition execution.

Do not use eval().

============================================================
20. MULTIPLE POLICY RULES
============================================================

Expense assessment may require more than one policy:

Example HOTEL:

POL-002:
hotel amount limit

POL-005:
receipt requirement

Therefore inspect whether the current PolicyRule model safely supports:

PolicyRule
or
list[PolicyRule]

If multiple rules are needed, extend the structured schema conservatively.

Suggested:

class PolicyRuleSet(BaseModel):
    rules: list[PolicyRule]
    source_chunk_ids: list[UUID]

or equivalent.

Do not discard receipt evidence just because amount-limit evidence exists.

Avoid overengineering a generic policy engine.

============================================================
21. CITATION VALIDATION
============================================================

Reuse Phase 003 citation validator.

Each rule/source citation must satisfy:

- chunk_id belongs to current reranked evidence;
- stored document status is ACTIVE;
- effective date is valid;
- expiry date is valid;
- policy/version/section metadata matches storage.

Build excerpts server-side.

Do not use LLM-generated excerpts as authoritative.

If zero valid policy citations remain:

decision = INSUFFICIENT_INFORMATION

Do not make a compliance decision.

============================================================
22. CONFIDENCE / EVIDENCE EVALUATION
============================================================

Implement a deterministic evidence/confidence layer.

This does NOT need a sophisticated ML confidence model.

Use available signals such as:

- valid citation count;
- retrieval availability;
- conflicting rules;
- structured PolicyRule validation;
- coverage of required conditions;
- reranker/retrieval scores where already available.

If:

no valid citations
OR
critical evidence is missing
OR
rules conflict materially

then:

decision = INSUFFICIENT_INFORMATION

Do not let model self-confidence be authoritative.

============================================================
23. EXPENSE SERVICE
============================================================

Implement/update:

backend/app/services/expense_service.py

Responsibilities:

1. create/retrieve expense business record;
2. create request/thread context;
3. invoke assessment graph;
4. persist assessment result;
5. map graph output to API schema;
6. preserve idempotency behavior;
7. surface domain errors.

Do not put:
- raw retrieval code;
- OpenAI calls;
- SQL in route;
- deterministic rules in route.

============================================================
24. REPOSITORIES
============================================================

Use repositories for persistence only.

Expected methods may include:

ExpenseRepository:
create()
get()
update_status()
save_assessment()

If assessment repository is separate, follow existing architecture.

Repository must not:
- call LLM;
- invoke graph;
- compute policy decision.

============================================================
25. TRANSACTION BOUNDARIES
============================================================

Follow this sequence:

1. validate input
2. create authoritative expense record
3. commit expense
4. invoke long-running retrieval/model workflow
5. persist assessment
6. update expense status if required
7. commit

Do not hold a database transaction open across long external model calls.

If workflow fails:
expense record may remain in a controlled state such as:
PENDING_ASSESSMENT
ASSESSMENT_FAILED

Use existing enums/conventions.

============================================================
26. API ROUTER
============================================================

Implement/update:

POST /api/v1/expenses

Router responsibilities only:

- input validation;
- request ID;
- idempotency key extraction if supported;
- call ExpenseService;
- map domain errors;
- return response.

No direct:
- DB queries;
- RAG calls;
- Model Gateway calls;
- rule evaluation.

============================================================
27. FRONTEND
============================================================

Implement the Expense Assessment UI using existing Phase 001/003 styles.

Expected components may include:

frontend/src/components/
    ExpenseForm.tsx
    DecisionCard.tsx
    CitationPanel.tsx

frontend/src/pages/
    ExpenseAssessmentPage.tsx

frontend/src/api/
    expenseApi.ts

Fields:

Expense Type
Amount
Currency
Location
Travel Type
Purpose
Receipt Available

Submit:

"Assess Expense"

Display:

Decision
Policy limit
Confidence
Explanation
Citations
Next action

Decision styles should visually distinguish:

COMPLIANT
NON_COMPLIANT
NEEDS_REVIEW
INSUFFICIENT_INFORMATION

Keep UI simple.

Do not build reviewer UI yet.

============================================================
28. NEXT_ACTION SEMANTICS
============================================================

Suggested values:

NONE
PROVIDE_CLARIFICATION
SUBMIT_EXCEPTION_JUSTIFICATION

For:

COMPLIANT
-> NONE

NON_COMPLIANT
-> NONE unless existing design says otherwise

NEEDS_REVIEW
-> SUBMIT_EXCEPTION_JUSTIFICATION

INSUFFICIENT_INFORMATION
-> PROVIDE_CLARIFICATION or RETRY/CONTACT_ADMIN depending on cause

Use existing enums if already defined.

Do not start Phase 005 workflow automatically.

============================================================
29. AUDIT / OBSERVABILITY
============================================================

Add lightweight events consistent with current architecture.

Capture:

request_id
thread_id
expense_id
scenario=expense_assessment

retrieval:
metadata_filters
lexical_count
vector_count
fused_count
reranked_count
chunk IDs
rrf score
rerank score

model:
task
provider
model
prompt_version
token usage
latency
retry count

decision:
policy rule type
policy limit
receipt requirement result
variance
valid citation count
confidence
final decision
abstention reason

Do not log:
API keys
secrets
full sensitive payloads unnecessarily

============================================================
30. ERROR MODEL
============================================================

Follow existing project error conventions.

Expected behavior:

Invalid request:
422

Duplicate idempotency key with different body:
409

No valid policy evidence:
return INSUFFICIENT_INFORMATION
not fabricated decision

Model temporarily unavailable:
503 or existing safe error behavior

Citation mismatch:
INSUFFICIENT_INFORMATION

PostgreSQL unavailable:
fail request
do not pretend persistence succeeded

Invalid structured PolicyRule:
one bounded repair/retry through Model Gateway if already supported
then safe failure

============================================================
31. TESTING
============================================================

Add comprehensive tests.

UNIT TESTS

A. Expense schema:
- valid HOTEL
- valid MEAL
- valid TAXI
- invalid amount <= 0
- invalid expense type
- invalid travel type
- Decimal preservation

B. Missing fields:
- each required field
- multiple missing fields

C. Deterministic rule engine:

Hotel:
6500 <= 7000
-> COMPLIANT

Hotel:
9500 > 7000
exception allowed
-> NEEDS_REVIEW

Receipt:
6500 > 500
receipt false
-> correct policy-defined failure path

Prohibition:
-> NON_COMPLIANT

No evidence:
-> INSUFFICIENT_INFORMATION

Conflicting evidence:
-> INSUFFICIENT_INFORMATION

D. PolicyRule model:
- Decimal limit
- valid UUID source IDs
- invalid rule type
- missing citations

E. Citation validation:
reuse Phase 003 tests where possible.

SERVICE TESTS

- expense is persisted before graph invocation;
- assessment persisted after graph success;
- graph failure leaves controlled expense state;
- idempotency behavior if supported.

GRAPH TESTS

- happy path compliant;
- over-limit NEEDS_REVIEW;
- missing fields;
- no evidence;
- receipt missing;
- citation invalid.

INTEGRATION TEST

POST /api/v1/expenses

Use mocked model/reranker when credentials unavailable.

Expected synthetic test:

{
  "expense_type": "HOTEL",
  "amount": "6500",
  "currency": "INR",
  "location": "Bengaluru",
  "travel_type": "DOMESTIC",
  "purpose": "Client meeting",
  "receipt_available": true
}

Expected:
decision = COMPLIANT
policy_limit = 7000
citation includes POL-002

Second case:

amount = 9500

Expected:
NEEDS_REVIEW
policy_limit = 7000
next_action = SUBMIT_EXCEPTION_JUSTIFICATION

No live OpenAI/Cohere dependency in CI.

============================================================
32. GOLDEN EXPENSE CASES
============================================================

Inspect:

evaluation/datasets/expense_cases.json

If present:
reuse and extend.

If absent:
create 8–12 deterministic smoke cases.

Include at least:

1.
Domestic hotel 6500 + receipt
-> COMPLIANT

2.
Domestic hotel 9500 + receipt
-> NEEDS_REVIEW

3.
International hotel 14000 + receipt
-> COMPLIANT

4.
International hotel 17000 + receipt
-> NEEDS_REVIEW

5.
Domestic meal 1200
-> COMPLIANT if policy applies

6.
Domestic meal 1800
-> NEEDS_REVIEW if exceptions allowed

7.
Airport taxi 1500
-> COMPLIANT

8.
Airport taxi 2500
-> NEEDS_REVIEW

9.
Expense > 500 with receipt missing
-> policy-defined NON_COMPLIANT/NEEDS_REVIEW

10.
No supporting policy
-> INSUFFICIENT_INFORMATION

These tests must derive expected facts from the synthetic policies.

============================================================
33. CONFIGURATION
============================================================

Reuse current config.

Expected relevant values:

RETRIEVAL_TOP_N=20
RRF_K=60
RERANK_TOP_K=5
MIN_CONFIDENCE=<existing>
CITATION_REQUIRED=true

No hardcoded:
OPENAI_API_KEY
COHERE_API_KEY
DB password

Keep all secrets environment-based.

============================================================
34. DATABASE MIGRATIONS
============================================================

Before creating migrations:

inspect existing Alembic versions.

Do not recreate Phase 002 RAG schema.

Only add missing Phase 004 business tables/columns if not already created.

Expected logical order from LLD:

extensions/schemas
business tables
policy document/chunk
FTS indexes
vector indexes
audit

If business tables already exist:
do not generate unnecessary duplicate migrations.

Always run:

python -m alembic current
python -m alembic upgrade head

and relevant migration tests.

============================================================
35. ARCHITECTURAL CONSTRAINTS
============================================================

Preserve:

API
 ->
Service
 ->
LangGraph
 ->
RAG
 +
Model Gateway
 +
Deterministic Rules
 +
Citation Validator
 ->
Business Persistence

Separation:

Probabilistic:
- extracting applicable rule
- summarizing explanation

Deterministic:
- amount comparison
- receipt checks
- prohibited rule
- routing threshold
- evidence sufficiency
- citation validity

PostgreSQL:
authoritative business state

LangGraph:
execution/orchestration state

Redis:
non-authoritative transient coordination

============================================================
36. DO NOT HARDCODE BUSINESS DECISION INTO LLM PROMPTS
============================================================

Bad:

"Given hotel is 9500 and limit is 7000, answer NEEDS_REVIEW."

Correct:

LLM returns:

{
  "rule_type": "AMOUNT_LIMIT",
  "category": "HOTEL",
  "amount_limit": "7000.00",
  "currency": "INR",
  "condition": "Domestic hotel per night",
  "source_chunk_ids": [...]
}

Then Python performs:

Decimal("9500") > Decimal("7000")

and returns NEEDS_REVIEW according to deterministic routing rules.

============================================================
37. IMPLEMENTATION ORDER
============================================================

Implement incrementally:

Step 1
Inspect completed 001/002/003 code.

Step 2
Inspect/create OpenSpec 004 artifacts.

Step 3
Validate OpenSpec.

Step 4
Inspect/complete business persistence models.

Step 5
Add/verify Alembic business migration.

Step 6
Implement Pydantic expense schemas.

Step 7
Implement missing-field detector.

Step 8
Extend LangGraph state.

Step 9
Reuse metadata filters.

Step 10
Reuse Hybrid RAG/RRF/reranker.

Step 11
Implement PolicyRule structured schema.

Step 12
Add Model Gateway EXPENSE_POLICY_RULE task.

Step 13
Implement extract_policy_rule node.

Step 14
Implement deterministic rule engine.

Step 15
Implement evaluate_expense node.

Step 16
Reuse citation validator.

Step 17
Implement deterministic evidence/confidence routing.

Step 18
Implement finalize assessment.

Step 19
Implement ExpenseRepository/service.

Step 20
Implement POST /api/v1/expenses.

Step 21
Implement React expense form.

Step 22
Implement result/decision UI.

Step 23
Add unit tests.

Step 24
Add graph tests.

Step 25
Add API/integration tests.

Step 26
Run migrations.

Step 27
Run backend tests.

Step 28
Run frontend build/tests.

Step 29
Validate OpenSpec.

Step 30
Update OpenSpec tasks.

STOP.

Do not begin Phase 005.

============================================================
38. REQUIRED VALIDATION COMMANDS
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

run locally supported:
openspec status
openspec validate
or equivalent discovered commands.

Do not invent unsupported OpenSpec flags.

If commands fail:
- show exact command;
- show exact error;
- fix if in scope;
- rerun.

============================================================
39. PHASE 004 ACCEPTANCE CRITERIA
============================================================

Phase 004 is complete only when:

[ ] OpenSpec 004 proposal/design/spec/tasks are valid

[ ] POST /api/v1/expenses exists

[ ] expense is persisted as business truth

[ ] assessment is persisted separately

[ ] money uses Decimal/NUMERIC

[ ] missing fields are handled deterministically

[ ] ACTIVE/effective policy filtering is reused

[ ] FTS retrieval is reused

[ ] pgvector retrieval is reused

[ ] RRF is reused

[ ] reranking is reused

[ ] PolicyRule is Pydantic validated

[ ] all LLM calls go through Model Gateway

[ ] LLM does not produce final compliance decision

[ ] amount threshold comparison is deterministic

[ ] receipt requirement check is deterministic

[ ] citations are validated

[ ] zero valid citations -> INSUFFICIENT_INFORMATION

[ ] COMPLIANT works

[ ] NON_COMPLIANT works when policy clearly requires it

[ ] NEEDS_REVIEW works

[ ] INSUFFICIENT_INFORMATION works

[ ] NEEDS_REVIEW does not start HITL yet

[ ] React expense form works

[ ] React displays policy citations

[ ] tests pass

[ ] frontend build passes

[ ] migrations are at head

[ ] no live model dependency required in CI

[ ] no secrets committed

[ ] OpenSpec tasks reflect actual status

============================================================
40. DEFINITION OF DONE DEMO
============================================================

Demo scenario 1:

Input:

HOTEL
INR 6500
Bengaluru
DOMESTIC
Client meeting
receipt = true

Expected processing:

persist expense
->
retrieve POL-002 + applicable documentation evidence
->
extract structured rule
->
validate citations
->
Python:
6500 <= 7000
->
COMPLIANT
->
persist assessment
->
return answer with citations

Demo scenario 2:

HOTEL
INR 9500
Bengaluru
DOMESTIC
Client meeting
receipt = true

Processing:

retrieve active POL-002 evidence
->
PolicyRule limit = 7000
->
Python:
9500 > 7000
->
exception allowed/review required
->
NEEDS_REVIEW
->
persist
->
next_action = SUBMIT_EXCEPTION_JUSTIFICATION

Do not invoke human review yet.

Demo scenario 3:

HOTEL
INR 6500
DOMESTIC
receipt = false

If POL-005 confirms receipt required:

apply deterministic receipt logic
->
policy-defined NON_COMPLIANT or NEEDS_REVIEW

Demo scenario 4:

No verified evidence

->
INSUFFICIENT_INFORMATION

Never fabricate a policy limit.

============================================================
41. FINAL IMPLEMENTATION REPORT
============================================================

After implementation provide:

1. OpenSpec files created/modified
2. backend files created/modified
3. frontend files created/modified
4. database migrations
5. schemas introduced/changed
6. graph nodes introduced/changed
7. deterministic rule logic
8. Model Gateway changes
9. API changes
10. tests added
11. commands executed
12. migration result
13. test results
14. frontend build result
15. OpenSpec validation result
16. known limitations
17. items deferred to Phase 005
18. concise end-to-end architecture flow

Do not merely say:
"implementation complete"

Show actual evidence.

STOP after Phase 004.
Do not proceed automatically to 005-exception-hitl.

## List of Phase-004 changes

Paths below are relative to `D:\git-repo\PolicyFlow-AI`. This is the Phase 004 implementation and validation inventory. The OpenSpec change is archived, while the working-tree files have not been committed or published.

### OpenSpec planning and requirements

- `openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/.openspec.yaml`
- `openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/proposal.md`
- `openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/design.md`
- `openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/specs/expense-compliance/spec.md`
- `openspec/changes/archive/2026-09-18-004-expense-compliance-assessment/tasks.md`
- `openspec/specs/expense-compliance/spec.md` (synced canonical capability spec)

### Database and backend

- `backend/alembic/versions/20260917_0003_expense_assessment.py`
- `backend/app/api/routes/expenses.py`
- `backend/app/core/exceptions.py`
- `backend/app/gateway/prompts.py`
- `backend/app/gateway/routing.py`
- `backend/app/graph/expense_graph.py`
- `backend/app/graph/graph.py`
- `backend/app/graph/state.py`
- `backend/app/main.py`
- `backend/app/models/assessment.py`
- `backend/app/models/expense.py`
- `backend/app/repositories/expense_repository.py`
- `backend/app/rules/__init__.py`
- `backend/app/rules/expense_rules.py`
- `backend/app/schemas/expense.py`
- `backend/app/services/expense_evidence.py`
- `backend/app/services/expense_rule_validation.py`
- `backend/app/services/expense_service.py`
- `backend/requirements.txt`

### Backend tests and evaluation data

- `backend/tests/test_expense_api.py`
- `backend/tests/test_expense_evidence.py`
- `backend/tests/test_expense_repository_integration.py`
- `backend/tests/test_expense_rule_extraction.py`
- `backend/tests/test_expense_rules.py`
- `backend/tests/test_expense_schema.py`
- `backend/tests/test_expense_workflow_integration.py`
- `backend/tests/test_policy_rag_integration.py` (updated expected Alembic head)
- `evaluation/datasets/expense_cases.json`

### Frontend

- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/api/expenseApi.ts`
- `frontend/src/api/types.ts`
- `frontend/src/pages/ExpensePage.tsx`

### Documentation

- `README.md`
- `docs/phase-004-local-validation.md`
- `docs/prompts/004-expense-compliance-assessment.md` (this repository copy of the Phase 004 brief)
- `D:\My Innovation Ideas\PolicyFlow AI\004-expense-compliance-assessment.md` (external copy updated with this list)

`backend/app/api/routes/policies.py` and `backend/tests/test_policy_qa.py` also have uncommitted changes, but they are a carried-over Phase 003 missing-key error fix rather than the Phase 004 expense feature. `frontend/tsconfig.tsbuildinfo` changed as generated TypeScript build metadata. Other current document moves/imports under `docs/` are not attributed to Phase 004 here.
