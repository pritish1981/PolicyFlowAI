You are acting as a Principal AI Engineer and Senior Python/React developer implementing the next OpenSpec change for the PolicyFlow AI project.

PROJECT
-------
Project name:
PolicyFlow AI — Enterprise Expense Compliance & Exception Agent

Repository root:
D:\git-repo\PolicyFlow-AI

Current OpenSpec change:
003-policy-qa

Source-of-truth documents:
- docs/requirements/PolicyFlow_AI_FRD_v1.0.docx
- docs/architecture/PolicyFlow_AI_HLD_v1.0.docx
- docs/architecture/PolicyFlow_AI_LLD_v1.0.docx
- openspec/project.md
- existing specifications under openspec/specs/
- current repository implementation

IMPORTANT
---------
Before modifying code:

1. Inspect the existing repository.
2. Read the OpenSpec project configuration.
3. Inspect:
   - openspec/specs/policy-rag/
   - openspec/specs/model-governance/
   - openspec/changes/001-platform-foundation/
   - openspec/changes/002-policy-ingestion-and-hybrid-rag/
   - openspec/changes/003-policy-qa/
4. Inspect the current implementation under:
   - backend/app/api/
   - backend/app/services/
   - backend/app/graph/
   - backend/app/rag/
   - backend/app/gateway/
   - backend/app/schemas/
   - backend/app/repositories/
   - frontend/src/
   - tests/
5. Reuse existing Phase 001 and Phase 002 functionality.
6. Do not rewrite working components unnecessarily.
7. Do not implement future phases unless a small interface/stub is required for Phase 003.
8. Do not skip OpenSpec artifacts.

PHASE 003 OBJECTIVE
-------------------
Implement the complete Policy Q&A use case:

User asks a natural-language expense-policy question.

Example:
"What is the maximum hotel reimbursement allowed for domestic travel?"

Expected flow:

React UI
    ->
POST /api/v1/policy/query
    ->
FastAPI + Pydantic validation
    ->
Policy Q&A application service
    ->
LangGraph POLICY_QA workflow
    ->
deterministic metadata filters
    ->
PostgreSQL FTS retrieval
+
pgvector semantic retrieval
    ->
RRF fusion
    ->
reranking
    ->
top 3-5 policy evidence chunks
    ->
Model Gateway
    ->
OpenAI grounded answer
    ->
citation validation
    ->
safe answer OR safe abstention
    ->
React answer + citations

The implementation must follow this architectural principle:

Retrieve evidence
-> interpret policy
-> validate citations
-> return grounded answer
-> abstain when evidence is insufficient

The LLM must NEVER invent policy thresholds or source references.

============================================================
1. OPEN SPEC WORKFLOW
============================================================

First inspect the existing 003-policy-qa change.

If proposal.md, design.md, specs, or tasks.md are incomplete, create/update them BEFORE implementation.

The OpenSpec change should describe only Phase 003.

Create/update:

openspec/changes/003-policy-qa/
    proposal.md
    design.md
    tasks.md
    specs/
        policy-qa/
            spec.md

Use the repository's existing OpenSpec style and conventions.

Do not invent a new format if the project already has a convention.

Proposal should clearly explain:
- why Policy Q&A is needed;
- what capability is introduced;
- what is explicitly out of scope;
- dependencies on Phase 002 hybrid RAG;
- impact on API, LangGraph, Model Gateway, frontend, tests.

Design should describe:
- API request/response;
- LangGraph path;
- metadata filtering;
- hybrid retrieval integration;
- RRF/reranking reuse;
- grounded generation;
- structured output;
- citation validation;
- abstention/error behavior;
- frontend flow;
- observability hooks;
- testing strategy.

Tasks should be implementation-oriented and checkbox-based.

After preparing OpenSpec artifacts:
- validate them using the locally available OpenSpec command/workflow;
- report validation errors before implementation;
- fix OpenSpec errors;
- only then proceed to code.

============================================================
2. STRICT PHASE 003 SCOPE
============================================================

IMPLEMENT:

A. Policy question API
B. Policy Q&A schemas
C. Policy service
D. LangGraph POLICY_QA path
E. deterministic metadata-filter construction
F. hybrid retrieval integration
G. RRF fusion integration
H. reranking integration
I. grounded-answer generation
J. Model Gateway invocation
K. structured output validation
L. citation construction and validation
M. safe abstention
N. Policy Q&A React screen
O. unit/integration tests
P. minimal tracing/logging metadata
Q. OpenSpec task completion

DO NOT IMPLEMENT:

- expense submission decisioning;
- COMPLIANT/NON_COMPLIANT computation;
- exception creation;
- HITL review;
- reviewer workflow;
- LangGraph human interrupt/resume;
- full expense assessment;
- AWS deployment;
- LangWatch dashboards;
- Ragas full evaluation suite;
- new database technology;
- Pinecone;
- DynamoDB;
- Kafka;
- Kubernetes;
- multi-agent architecture.

Those belong to later phases.

============================================================
3. API CONTRACT
============================================================

Implement or complete:

POST /api/v1/policy/query

Suggested request:

{
  "question": "What is the maximum hotel reimbursement allowed for domestic travel?",
  "category": "HOTEL",
  "region": "INDIA"
}

Only question should be required unless current project contracts already define otherwise.

Suggested Pydantic model:

class PolicyQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    category: str | None = None
    region: str | None = None

Response should contain:

{
  "request_id": "...",
  "answer": "...",
  "citations": [
    {
      "chunk_id": "...",
      "policy_code": "POL-002",
      "policy_version": "1.0",
      "section_id": "...",
      "section_title": "Domestic Hotel Limit",
      "excerpt": "..."
    }
  ],
  "evidence_status": "GROUNDED"
}

Define a controlled evidence_status enum, for example:

GROUNDED
INSUFFICIENT_INFORMATION

Do not return fabricated answers when retrieval/citation requirements fail.

Use existing error-response conventions if already present.

============================================================
4. POLICY Q&A LANGGRAPH FLOW
============================================================

Implement a minimal Phase 003 LangGraph path.

Use the existing graph structure if already created.

State should include only the fields needed now, while staying compatible with the LLD ExpenseState.

Relevant fields:

request_id
thread_id if already required by framework
scenario
user_query
metadata_filters
lexical_hits
vector_hits
fused_hits
reranked_hits
citations
answer
evidence_status
model_usage
errors

Expected graph:

START
  ->
validate_request
  ->
classify_intent or explicitly set scenario=policy_qa
  ->
build_metadata_filters
  ->
hybrid_retrieve
  ->
fuse_results
  ->
rerank_results
  ->
generate_grounded_answer
  ->
validate_citations
  ->
final_response
  ->
END

IMPORTANT:
Do not add expense/HITL branches for Phase 003 unless required to preserve an existing shared graph skeleton.

============================================================
5. REQUEST VALIDATION
============================================================

Implement deterministic validation:

- question cannot be blank;
- trim whitespace;
- enforce max length;
- reject unsupported request shape;
- request_id must be generated or propagated;
- sanitize logs;
- do not log API keys or secrets.

Do not use an LLM for request validation.

============================================================
6. METADATA FILTERING
============================================================

Implement deterministic metadata filters before/with retrieval.

Always enforce:

status = ACTIVE

Also consider:

effective_date <= current assessment date

and if expiry date exists:

assessment_date < expiry_date

Optional filters based on user input or deterministic classification:

category
region

Do not let the LLM decide whether inactive/expired policies are allowed.

Do not filter so aggressively that normal policy questions produce zero results simply due to missing optional metadata.

============================================================
7. HYBRID RETRIEVAL
============================================================

Reuse Phase 002 retrieval components.

Expected structure currently includes:

backend/app/rag/retrieval/
    lexical_retriever.py
    vector_retriever.py
    hybrid_retriever.py
    rrf.py

Use:

PostgreSQL FTS top 20
+
pgvector semantic top 20

Initial parameters:

LEXICAL_TOP_N = 20
VECTOR_TOP_N = 20
RRF_K = 60

Preserve retrieval metadata:

chunk_id
policy_code
policy_version
section_id
section_title
content
lexical_rank
vector_rank
rrf_score
metadata

Deduplicate by chunk_id before reranking.

No new vector database is allowed.

============================================================
8. RRF
============================================================

Implement or reuse Reciprocal Rank Fusion:

score(document) =
SUM(1 / (k + rank_i(document)))

Use:

k = 60

Requirements:

- deterministic;
- unit-testable;
- chunk_id as identity;
- preserve source ranks;
- sort descending by rrf_score;
- handle chunk appearing in only one retrieval list;
- no duplicate final candidates.

============================================================
9. RERANKING
============================================================

Reuse the Phase 002 reranker abstraction.

Expected repository structure:

backend/app/rag/reranking/
    base.py
    cohere_reranker.py
    bge_reranker.py

Desired behavior:

fused top 10-20
    ->
reranker
    ->
top 3-5 evidence chunks

Preferred provider:
Cohere reranker

Optional fallback:
BGE adapter

Do not embed Cohere calls directly inside graph nodes.

Graph node should depend on a reranker interface/service.

If credentials are unavailable in tests, mock the reranker.

============================================================
10. MODEL GATEWAY
============================================================

All LLM calls MUST go through:

backend/app/gateway/

Expected modules:

model_gateway.py
routing.py
token_control.py
retry.py
providers/base.py
providers/openai_provider.py

Do not call OpenAI SDK directly from:

API route
service
LangGraph node
RAG retriever
citation validator

If the Model Gateway is not fully implemented yet:
implement the smallest production-oriented interface needed for Policy Q&A.

Suggested interface:

class ModelGateway(Protocol):

    async def invoke_structured(
        self,
        task: ModelTask,
        messages: list,
        output_schema: type[BaseModel],
        context: ModelContext,
    ) -> BaseModel:
        ...

Create/use task:

POLICY_QA

The gateway owns:
- provider invocation;
- model routing;
- timeout;
- retries;
- token limits;
- structured response validation;
- model metadata.

Keep it compatible with Phase 006 where Model Gateway guardrails will be expanded.

============================================================
11. GROUNDED ANSWER OUTPUT
============================================================

Create a strict Pydantic structured model.

Suggested:

class GroundedPolicyAnswer(BaseModel):
    answer: str
    citation_chunk_ids: list[UUID]
    insufficient_information: bool = False

Prompt requirements:

SYSTEM:
You answer enterprise expense-policy questions only from the supplied policy evidence.

RULES:
1. Use only supplied evidence.
2. Never invent thresholds, policy names, versions, sections, or exceptions.
3. Every material policy statement must map to an evidence chunk.
4. Reference chunk IDs exactly as supplied.
5. If evidence does not support an answer, return insufficient_information=true.
6. Do not decide employee expense compliance.
7. Do not approve exceptions.
8. Do not use external knowledge.

USER INPUT:
question

CONTEXT:
top reranked chunks with:
- chunk_id
- policy_code
- version
- section title
- content

Do not ask the model to produce free-form citation excerpts.

============================================================
12. CITATION VALIDATION
============================================================

Citation validation MUST be deterministic.

Use the LLD algorithm.

For each returned citation_chunk_id:

1. citation chunk ID must be in reranked_hits;
2. document status must be ACTIVE;
3. effective date must be valid;
4. expiry date must not invalidate it;
5. stored policy_code/version/section must match;
6. citation excerpt is created server-side from stored chunk content.

Never trust a model-generated excerpt.

If a material answer has zero valid citations:

return safe abstention:

evidence_status = INSUFFICIENT_INFORMATION

Suggested user response:

"I could not find enough verified policy evidence to answer this question reliably."

Do NOT hallucinate.

============================================================
13. POLICY SERVICE
============================================================

Implement/update:

backend/app/services/policy_service.py

Responsibilities:

- create request context;
- invoke Policy Q&A graph/use case;
- map graph result to response schema;
- enforce response contract.

The API router should stay thin.

Do not put retrieval/model/business logic into the FastAPI route.

============================================================
14. API ROUTER
============================================================

Implement/update:

backend/app/api/routes/policies.py

Responsibilities only:

- receive request;
- Pydantic validation;
- correlation/request ID;
- call PolicyService;
- map known domain errors to HTTP responses;
- return PolicyAnswerResponse.

No direct database queries.
No direct RAG calls.
No OpenAI calls.

Register router in main.py if not already registered.

============================================================
15. FRONTEND
============================================================

Implement the Policy Q&A UI using existing structure:

frontend/src/api/policyApi.ts

frontend/src/components/
    PolicyQuestion.tsx
    CitationPanel.tsx

frontend/src/pages/
    PolicyQApage.tsx

Requirements:

PolicyQuestion:
- text question input;
- submit button;
- loading state;
- input validation.

PolicyQApage:
- call POST /api/v1/policy/query;
- display grounded answer;
- display evidence status;
- error handling;
- insufficient-information state.

CitationPanel:
show:
- policy code;
- version;
- section title;
- excerpt.

Keep UI simple and professional.

Do not implement expense forms or reviewer UI in this change.

Example question shown in UI:

"What is the maximum hotel reimbursement allowed for domestic travel?"

Expected synthetic answer should be grounded in POL-002 and indicate INR 7,000/night if that policy is active and retrieved.

============================================================
16. TESTING
============================================================

Add tests at the correct existing locations.

UNIT TESTS

Minimum:

test metadata filters:
- ACTIVE enforced
- optional category
- optional region

test RRF:
- lexical only
- vector only
- common hit
- ordering
- duplicate chunk ID

test citation validator:
- valid citation
- unknown chunk ID
- inactive policy
- expired policy
- metadata mismatch
- zero valid citations

test grounded answer schema:
- valid structured response
- invalid chunk ID format
- insufficient_information

SERVICE TESTS:
- grounded Q&A result
- insufficient evidence
- gateway failure handling

INTEGRATION TEST:

POST /api/v1/policy/query

Use mocked gateway/reranker if external credentials are unavailable.

Expected:
HTTP 200

answer exists
citation exists
policy_code = POL-002 for hotel limit query

Also test:
no evidence
-> safe abstention

Do not require live OpenAI/Cohere credentials in CI.

============================================================
17. GOLDEN POLICY QA DATASET
============================================================

If evaluation/datasets/policy_qa_golden.json already exists, inspect and reuse it.

Otherwise create a small Phase 003 deterministic smoke dataset.

Include approximately 8-12 queries.

Examples:

1.
Question:
"What is the maximum hotel reimbursement allowed for domestic travel?"

Expected policy:
POL-002

Expected fact:
7000

2.
Question:
"What is the hotel limit for international travel?"

Expected:
POL-002
15000

3.
Question:
"What is the daily meal allowance for domestic travel?"

Expected:
POL-003
1500

4.
Question:
"What is the airport taxi limit?"

Expected:
POL-004
2000

5.
Question:
"When is a receipt mandatory?"

Expected:
POL-005
amount > 500

6.
Question:
"What happens if my hotel expense exceeds the standard limit?"

Expected:
POL-006 / POL-002
human exception review

Do not implement full Ragas/DeepEval in this phase unless already available.

Only add smoke validation needed for Phase 003.

============================================================
18. CONFIGURATION
============================================================

Reuse existing configuration mechanisms.

Expected values:

RETRIEVAL_TOP_N=20
RRF_K=60
RERANK_TOP_K=5
CITATION_REQUIRED=true

Embedding/model settings must come from config/environment.

No API key may be hardcoded.

Do not commit:
OPENAI_API_KEY
COHERE_API_KEY
database password
other secrets

============================================================
19. OBSERVABILITY
============================================================

Add lightweight structured logging/tracing hooks.

Capture:

request_id
scenario=policy_qa
metadata_filters
lexical_count
vector_count
fused_count
reranked_count
retrieved_chunk_ids
rrf_score
rerank_score where available
citation_valid_count
model/provider
model latency if gateway provides it
token usage if gateway provides it
evidence_status

Do not log entire policy documents unnecessarily.

Do not log secrets.

============================================================
20. ERROR BEHAVIOR
============================================================

Follow current project error model.

Expected scenarios:

Invalid question
-> 422

No policy evidence
-> safe PolicyAnswerResponse with INSUFFICIENT_INFORMATION
   OR existing documented endpoint convention

Model unavailable
-> 503

Reranker unavailable
-> use configured safe fallback to fused ranking if project config permits,
   otherwise safe failure

Citation mismatch
-> reject model conclusion
-> return INSUFFICIENT_INFORMATION

PostgreSQL unavailable
-> fail request
-> never pretend retrieval succeeded

============================================================
21. ARCHITECTURAL CONSTRAINTS
============================================================

Preserve these boundaries:

API
  -> Service
      -> Graph
          -> RAG
          -> Model Gateway
          -> Citation Validator

Repositories only handle persistence/query concerns.

No direct provider SDK in graph nodes.

No policy logic in API routers.

No authoritative decision from LLM.

No autonomous exception approval.

No new architecture stack unless required by existing source-of-truth documents.

============================================================
22. IMPLEMENTATION ORDER
============================================================

Implement incrementally in this order:

Step 1
Inspect repository and OpenSpec state.

Step 2
Create/update OpenSpec:
proposal
design
spec
tasks

Step 3
Validate OpenSpec.

Step 4
Implement Policy Q&A Pydantic schemas.

Step 5
Implement/update deterministic metadata-filter builder.

Step 6
Wire existing hybrid retriever.

Step 7
Wire RRF.

Step 8
Wire reranker.

Step 9
Implement Model Gateway POLICY_QA task.

Step 10
Implement grounded-answer prompt + structured model.

Step 11
Implement deterministic citation validator.

Step 12
Implement Policy Q&A LangGraph path.

Step 13
Implement PolicyService.

Step 14
Implement FastAPI route.

Step 15
Implement frontend Policy Q&A page/components.

Step 16
Add unit tests.

Step 17
Add integration tests.

Step 18
Run backend test suite.

Step 19
Run frontend build/tests.

Step 20
Run OpenSpec validation.

Step 21
Update OpenSpec task completion status.

Do NOT proceed to 004-expense-compliance-assessment.

============================================================
23. REQUIRED VALIDATION COMMANDS
============================================================

Use the project's actual environment/tooling discovered from the repository.

At minimum attempt:

Backend:

python -m pytest -v

or targeted first:

python -m pytest tests/unit -v

python -m pytest tests/integration -v

Frontend:

npm run build

If frontend tests exist:

npm test

Database:
verify migrations are current if this phase modifies schema.

OpenSpec:
run the locally supported OpenSpec validation/status command.
Do not assume unsupported flags.

If a command fails:
- report exact command;
- report exact error;
- fix code/config if within scope;
- rerun.

============================================================
24. ACCEPTANCE CRITERIA
============================================================

Phase 003 is complete only when:

[ ] OpenSpec 003-policy-qa proposal/design/spec/tasks are valid

[ ] POST /api/v1/policy/query is implemented

[ ] Natural-language policy question can be submitted

[ ] ACTIVE/effective metadata filtering is deterministic

[ ] FTS retrieval is used

[ ] pgvector semantic retrieval is used

[ ] RRF combines lexical/vector results

[ ] Reranking produces top 3-5 evidence chunks

[ ] All LLM calls go through Model Gateway

[ ] Output is Pydantic-validated

[ ] Answer uses retrieved evidence only

[ ] Citation chunk IDs must originate from reranked evidence

[ ] Citation metadata is validated against stored records

[ ] Citation excerpts are created server-side

[ ] Zero valid citations results in safe abstention

[ ] React page displays answer + citations

[ ] Synthetic hotel query resolves to POL-002 when corpus is correctly ingested

[ ] Unit tests pass

[ ] Integration tests pass

[ ] Frontend build passes

[ ] No live external model credentials required in CI tests

[ ] No secrets committed

[ ] OpenSpec validation passes

[ ] OpenSpec tasks reflect actual implementation state

============================================================
25. DEFINITION OF DONE DEMO
============================================================

The following should work end-to-end:

User asks:

"What is the maximum hotel reimbursement allowed for domestic travel?"

System:

1. receives question;
2. validates request;
3. identifies policy-qa scenario;
4. filters ACTIVE policy content;
5. retrieves lexical candidates;
6. retrieves vector candidates;
7. applies RRF;
8. reranks evidence;
9. sends only top evidence to Model Gateway;
10. obtains structured grounded answer;
11. validates citation IDs;
12. builds citations from stored chunks;
13. returns:

answer:
"The standard domestic hotel reimbursement limit is INR 7,000 per night ..."

citation:
POL-002
Hotel & Accommodation Policy
Domestic Hotel Limit section

The answer must only contain INR 7,000 if retrieved evidence actually supports it.

If the policy evidence is missing:
return INSUFFICIENT_INFORMATION rather than inventing INR 7,000.

============================================================
26. FINAL REPORT
============================================================

When implementation is finished, provide:

1. OpenSpec files created/modified
2. Backend files created/modified
3. Frontend files created/modified
4. Tests created/modified
5. Configuration changes
6. Database/migration changes, if any
7. Commands executed
8. Test results
9. Frontend build result
10. OpenSpec validation result
11. Known limitations
12. Items intentionally deferred to Phase 004+
13. concise end-to-end flow summary

Do not just say "implemented successfully."

Show actual validation results.

STOP after Phase 003 is complete.
Do not begin Phase 004 automatically.

## Files updated/modified during this phase
Based on the Phase 003 OpenSpec scope and implementation, these are the files created or updated for this phase.

##OpenSpec
- [proposal.md](D:/git-repo/PolicyFlow-AI/openspec/changes/003-policy-qa/proposal.md)
- [design.md](D:/git-repo/PolicyFlow-AI/openspec/changes/003-policy-qa/design.md)
- [policy-qa/spec.md](D:/git-repo/PolicyFlow-AI/openspec/changes/003-policy-qa/specs/policy-qa/spec.md)
- [tasks.md](D:/git-repo/PolicyFlow-AI/openspec/changes/003-policy-qa/tasks.md)
##Backend contracts and configuration
- [config.py](D:/git-repo/PolicyFlow-AI/backend/app/core/config.py)
- [exceptions.py](D:/git-repo/PolicyFlow-AI/backend/app/core/exceptions.py)
- [policy.py](D:/git-repo/PolicyFlow-AI/backend/app/schemas/policy.py)
- [.env.example](D:/git-repo/PolicyFlow-AI/.env.example)
- [docker-compose.yml](D:/git-repo/PolicyFlow-AI/docker-compose.yml)
- [requirements.txt](D:/git-repo/PolicyFlow-AI/backend/requirements.txt)
##Retrieval, reranking, and citation controls
- [hybrid_retriever.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/hybrid_retriever.py)
- [rrf.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/rrf.py)
- [reranking/__init__.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/__init__.py)
- [reranking/base.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/base.py)
- [cohere_reranker.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/cohere_reranker.py)
- [bge_reranker.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/bge_reranker.py)
- [citations/validator.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/citations/validator.py)
##Model Gateway
- [model_gateway.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/model_gateway.py)
- [prompts.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/prompts.py)
- [routing.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/routing.py)
- [retry.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/retry.py)
- [token_control.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/token_control.py)
- [providers/base.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/providers/base.py)
- [providers/openai_provider.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/providers/openai_provider.py)
- [gateway/__init__.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/__init__.py)
- [providers/__init__.py](D:/git-repo/PolicyFlow-AI/backend/app/gateway/providers/__init__.py)
##LangGraph, service, and API
- [graph/state.py](D:/git-repo/PolicyFlow-AI/backend/app/graph/state.py)
- [graph/graph.py](D:/git-repo/PolicyFlow-AI/backend/app/graph/graph.py)
- [policy_service.py](D:/git-repo/PolicyFlow-AI/backend/app/services/policy_service.py)
- [api/routes/policies.py](D:/git-repo/PolicyFlow-AI/backend/app/api/routes/policies.py)
- [main.py](D:/git-repo/PolicyFlow-AI/backend/app/main.py)
- [api/v1/policy.py](D:/git-repo/PolicyFlow-AI/backend/app/api/v1/policy.py) — retained/adjusted as the Phase 002 compatibility surface.
##Frontend
- [policyApi.ts](D:/git-repo/PolicyFlow-AI/frontend/src/api/policyApi.ts)
- [types.ts](D:/git-repo/PolicyFlow-AI/frontend/src/api/types.ts)
- [PolicyQuestion.tsx](D:/git-repo/PolicyFlow-AI/frontend/src/components/PolicyQuestion.tsx)
- [CitationPanel.tsx](D:/git-repo/PolicyFlow-AI/frontend/src/components/CitationPanel.tsx)
- [PolicyQAPage.tsx](D:/git-repo/PolicyFlow-AI/frontend/src/pages/PolicyQAPage.tsx)
- [App.tsx](D:/git-repo/PolicyFlow-AI/frontend/src/App.tsx)
- [App.css](D:/git-repo/PolicyFlow-AI/frontend/src/App.css)
##Tests and evaluation data
- [test_policy_qa.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_qa.py)
- [test_policy_api_adapters.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_api_adapters.py)
- [test_policy_rag.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_rag.py)
- [test_policy_rag_integration.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_rag_integration.py)
- [policy_qa_golden.json](D:/git-repo/PolicyFlow-AI/evaluation/datasets/policy_qa_golden.json)
##During the final completion pass specifically, I directly changed:
- backend/tests/test_policy_qa.py
- backend/tests/test_policy_api_adapters.py
- docker-compose.yml
- openspec/changes/003-policy-qa/tasks.md