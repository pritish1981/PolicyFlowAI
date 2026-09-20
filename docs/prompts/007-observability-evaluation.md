You are acting as a Principal AI Engineer and Senior Python developer implementing the next OpenSpec change for the PolicyFlow AI project.

PROJECT
-------
Project name:
PolicyFlow AI — Enterprise Expense Compliance & Exception Agent

Repository root:
D:\git-repo\PolicyFlow-AI

Current OpenSpec change:
007-observability-evaluation

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
  - 005-exception-hitl
  - 006-model-gateway-guardrails
- current repository implementation

PRIMARY TECHNOLOGY CHOICE FOR THIS PHASE
----------------------------------------
Runtime observability:
- LangSmith

Offline evaluation:
- Ragas
- DeepEval
- Pytest

Installation command:

python -m pip install langsmith ragas deepeval

============================================================
0. BEFORE WRITING CODE
============================================================

Before modifying any source code:

1. Inspect the full repository.
2. Read OpenSpec project conventions.
3. Inspect:
   - openspec/changes/007-observability-evaluation/
   - openspec/specs/
   - evaluation/
   - backend/app/observability/
   - backend/app/gateway/
   - backend/app/graph/
   - backend/app/rag/
   - backend/tests/
4. Inspect completed changes 003 through 006 carefully.
5. Identify current:
   - logging
   - model telemetry
   - graph tracing
   - retrieval metadata
   - token usage
   - prompt versions
   - citations
   - decision metadata
6. Identify whether LangSmith is already indirectly installed.
7. Do not duplicate observability already implemented.
8. Do not change working business logic merely to add traces.
9. Do not change deterministic expense decision semantics.
10. Do not change HITL authority boundaries.
11. Do not implement AWS/CloudWatch infrastructure beyond interfaces/hooks.
12. Do not begin Phase 008.
13. Do not require live OpenAI calls in CI evaluation.

Before coding, provide:

- current observability state;
- existing evaluation assets;
- instrumentation gaps;
- proposed file changes;
- exact implementation order.

============================================================
1. PHASE 007 OBJECTIVE
============================================================

Implement production-oriented AI observability and offline evaluation for PolicyFlow AI.

This phase has TWO distinct responsibilities:

A. Runtime Observability
   using LangSmith

B. Offline / CI Quality Evaluation
   using:
   - Ragas
   - DeepEval
   - Pytest
   - golden datasets

Target architecture:

PolicyFlow Request
      |
      v
FastAPI
      |
      v
LangGraph
      |
      +--> Retrieval
      |
      +--> RRF
      |
      +--> Reranker
      |
      +--> Model Gateway
      |
      +--> Deterministic Rules
      |
      +--> Citation Validation
      |
      +--> HITL
      |
      v
Final Result

Every important AI workflow stage should expose traceable metadata.

Runtime:
    LangSmith

Offline:
    Golden Dataset
       |
       +--> Retrieval evaluation
       +--> RAG answer evaluation
       +--> citation evaluation
       +--> deterministic decision evaluation
       +--> regression tests

============================================================
2. OPENSPEC WORKFLOW
============================================================

Inspect:

openspec/changes/007-observability-evaluation/

If incomplete, create/update:

openspec/changes/007-observability-evaluation/
    proposal.md
    design.md
    tasks.md
    specs/
        observability-evaluation/
            spec.md

Follow project OpenSpec conventions exactly.

Proposal must explain:

- why runtime AI observability is needed;
- why normal application logs are insufficient;
- why LangSmith is chosen;
- why evaluation must remain separate from runtime requests;
- why golden datasets are required;
- Ragas responsibilities;
- DeepEval responsibilities;
- Pytest responsibilities;
- regression/evaluation goals;
- explicit out-of-scope items.

Design must cover:

- trace hierarchy;
- request/thread correlation;
- graph node tracing;
- retrieval telemetry;
- Model Gateway telemetry;
- token/cost metadata;
- latency;
- prompt version;
- decision/citation metadata;
- privacy/redaction;
- golden dataset format;
- retrieval metrics;
- RAG metrics;
- deterministic decision metrics;
- evaluation runners;
- CI behavior;
- failure thresholds;
- baseline comparisons;
- report generation.

Validate OpenSpec before coding.

============================================================
3. STRICT PHASE 007 SCOPE
============================================================

IMPLEMENT:

A. LangSmith integration
B. LangGraph trace propagation
C. Model Gateway tracing
D. retrieval tracing
E. RRF/reranker metadata
F. citation-validation metadata
G. deterministic-decision metadata
H. HITL interrupt/resume trace markers
I. request/thread correlation
J. token usage tracking
K. latency tracking
L. retry/fallback tracking
M. prompt-version tracking
N. golden datasets
O. Ragas evaluation
P. DeepEval evaluation
Q. Pytest regression gates
R. vector-only vs hybrid vs hybrid+rerank benchmark
S. evaluation reports
T. documentation
U. OpenSpec completion

DO NOT IMPLEMENT:

- AWS CloudWatch infrastructure;
- Grafana;
- Prometheus;
- full production alerting;
- real customer telemetry;
- confidential data logging;
- new business flows;
- new RAG algorithm;
- new model provider;
- new vector database;
- Phase 008 deployment.

============================================================
4. DEPENDENCIES
============================================================

Install:

python -m pip install langsmith ragas deepeval

Add pinned or compatible versions to:

backend/requirements.txt

or the project's dependency management file.

Do not hardcode API keys.

Update .env.example with placeholders only.

============================================================
5. LANGSMITH CONFIGURATION
============================================================

Expected environment configuration:

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=policyflow-ai-dev

Optionally support:

LANGSMITH_ENDPOINT=

if current environment requires it.

Do not fail the application startup solely because LangSmith is disabled.

Observability should be configurable.

Expected behavior:

LANGSMITH_TRACING=false
or no API key
    ->
application still works
    ->
tracing disabled safely

============================================================
6. TRACE CORRELATION
============================================================

Every trace should correlate:

request_id
thread_id

Where relevant also include:

expense_id
exception_id
review_id

These identifiers should allow an engineer to follow:

API request
    ->
LangGraph execution
    ->
retrieval
    ->
model call
    ->
decision
    ->
HITL
    ->
final result

Do not generate unrelated correlation IDs at every layer.

Reuse existing IDs.

============================================================
7. LANGSMITH TRACE HIERARCHY
============================================================

Create a clear logical trace hierarchy.

Example:

PolicyFlow Request
|
+-- API
|
+-- LangGraph
|    |
|    +-- validate_request
|    +-- build_metadata_filters
|    +-- hybrid_retrieve
|    +-- rrf_fusion
|    +-- rerank
|    +-- model_gateway
|    +-- deterministic_rules
|    +-- citation_validation
|    +-- evaluate_confidence
|    +-- human_review
|    +-- finalize
|
+-- Final Result

Avoid tracing trivial helper functions unless useful.

Trace business-relevant stages.

============================================================
8. GRAPH NODE OBSERVABILITY
============================================================

Capture for each major LangGraph node:

node_name
request_id
thread_id
scenario
start time
end time
duration_ms
success/failure
error category if failed

Do not log full graph state.

Log IDs and summarized metadata only.

============================================================
9. RETRIEVAL OBSERVABILITY
============================================================

For every retrieval call capture:

query_id / request_id
metadata_filters

lexical_count
vector_count
fused_count
reranked_count

retrieved_chunk_ids
reranked_chunk_ids

lexical ranks
vector ranks
rrf scores
reranker scores

Do not log full document contents to external telemetry unless explicitly enabled.

Chunk IDs and metadata are preferred.

============================================================
10. MODEL GATEWAY OBSERVABILITY
============================================================

Reuse Phase 006 telemetry.

Capture:

task
provider
model
prompt_version

input_tokens
output_tokens
total_tokens

latency_ms

retry_count
validation_retry_count
fallback_used

error_category

request_id
thread_id

Do not duplicate provider-specific tracing outside the gateway.

============================================================
11. DECISION OBSERVABILITY
============================================================

For expense assessment capture:

expense_id
expense_type
policy_rule_type
policy_limit if safe
decision
confidence
citation_valid_count
abstention_reason

Do not send excessive sensitive expense details into LangSmith.

Prefer metadata.

============================================================
12. CITATION OBSERVABILITY
============================================================

Capture:

citation_count_generated
citation_count_valid
invalid_citation_count
citation_chunk_ids

If validation fails:

capture reason category such as:

CHUNK_NOT_RETRIEVED
INACTIVE_POLICY
VERSION_MISMATCH
EXPIRED_POLICY
METADATA_MISMATCH

Do not expose entire policy text unnecessarily.

============================================================
13. HITL OBSERVABILITY
============================================================

Trace:

HUMAN_REVIEW_INTERRUPTED

and:

WORKFLOW_RESUMED

Capture:

thread_id
exception_id
review status
review action

Do not log reviewer comments in full unless explicitly configured.

The human decision remains authoritative business state.

LangSmith is telemetry only.

============================================================
14. ERROR OBSERVABILITY
============================================================

Normalize trace error categories.

Examples:

VALIDATION_ERROR
RETRIEVAL_ERROR
RERANKER_ERROR
MODEL_TIMEOUT
MODEL_RATE_LIMIT
MODEL_VALIDATION_ERROR
GUARDRAIL_VIOLATION
CITATION_FAILURE
WORKFLOW_STATE_CONFLICT
DATABASE_ERROR

Do not expose raw secrets/provider credentials.

============================================================
15. PRIVACY / REDACTION
============================================================

Implement telemetry minimization.

Do not send:

API keys
authorization headers
database credentials
secrets
raw user PII
full justifications unless explicitly necessary
full policy documents

Prefer:

IDs
counts
scores
categories
status
prompt versions
token counts
latency

Create a helper such as:

sanitize_trace_metadata()

if appropriate.

============================================================
16. OBSERVABILITY MODULE
============================================================

Use or extend:

backend/app/observability/

Suggested files:

backend/app/observability/
    tracing.py
    metrics.py
    context.py
    redaction.py

Do not create unnecessary abstractions if equivalent files already exist.

Possible responsibilities:

tracing.py
- LangSmith setup
- trace/span helpers

context.py
- request/thread metadata

redaction.py
- safe telemetry filtering

metrics.py
- structured metric helpers

============================================================
17. OPTIONAL LANGSMITH DECORATORS / CONTEXT
============================================================

Use LangSmith native tracing patterns compatible with installed versions.

Do not hardcode APIs without checking installed LangSmith SDK.

Prefer official constructs supported by current version.

Possible approaches:
- traceable decorators
- tracing context
- LangGraph native tracing integration

Inspect existing LangGraph integration first.

Do not double-trace the same model call.

============================================================
18. GOLDEN DATASETS
============================================================

Inspect:

evaluation/datasets/

Expected files:

policy_qa_golden.json
expense_cases.json

If present:
reuse and extend.

Create a minimum meaningful dataset.

Recommended:

Policy Q&A:
10-20 cases

Expense assessment:
10-20 cases

Exception/HITL:
5-10 cases if useful

Keep total POC dataset manageable.

Each case should include expected evidence.

============================================================
19. POLICY Q&A GOLDEN DATA FORMAT
============================================================

Suggested:

{
  "id": "hotel-domestic-limit-01",
  "query": "What is the maximum hotel reimbursement allowed for domestic travel?",
  "expected_policy_code": "POL-002",
  "expected_section": "...",
  "expected_facts": {
    "amount": 7000,
    "currency": "INR"
  }
}

Include cases for:

POL-001
POL-002
POL-003
POL-004
POL-005
POL-006

Include at least some paraphrased questions.

============================================================
20. EXPENSE GOLDEN DATA FORMAT
============================================================

Suggested:

{
  "id": "hotel-domestic-over-limit-01",
  "expense": {
    "expense_type": "HOTEL",
    "amount": "9500.00",
    "currency": "INR",
    "location": "Bengaluru",
    "travel_type": "DOMESTIC",
    "purpose": "Client meeting",
    "receipt_available": true
  },
  "expected_policy_code": "POL-002",
  "expected_limit": "7000.00",
  "expected_decision": "NEEDS_REVIEW"
}

Include:

COMPLIANT
NON_COMPLIANT
NEEDS_REVIEW
INSUFFICIENT_INFORMATION

============================================================
21. RETRIEVAL METRICS
============================================================

Implement deterministic retrieval metrics.

At minimum:

Precision@5
Recall@10

Optional:

MRR
NDCG

Definitions:

Precision@5:
how many of the top 5 retrieved items are relevant.

Recall@10:
whether relevant expected evidence is included within top 10.

MRR:
position of first correct result.

Do not depend on LLM-as-judge for these metrics.

============================================================
22. CITATION CORRECTNESS METRIC
============================================================

Implement deterministic citation correctness.

Questions:

Did returned citation:
- belong to retrieved evidence?
- point to expected policy?
- point to expected section where specified?
- remain active/effective?

Metric can be:

correct citations / total citations

Also track:

percentage of responses with >=1 valid citation.

============================================================
23. RAGAS EVALUATION
============================================================

Use Ragas for RAG quality evaluation.

Inspect current Ragas API version before implementing.

Do not assume old/deprecated APIs.

Target metrics where compatible:

faithfulness
answer relevance
context relevance / context precision
context recall

Use only metrics supported by installed version.

Evaluation pipeline:

golden dataset
    ->
run PolicyFlow Q&A
    ->
capture:
query
answer
contexts
reference answer/facts
    ->
Ragas evaluation
    ->
report metrics

Do not run Ragas inside normal API requests.

============================================================
24. DEEPEVAL EVALUATION
============================================================

Use DeepEval for complementary AI evaluation.

Inspect installed DeepEval version first.

Possible metrics where supported:

FaithfulnessMetric
AnswerRelevancyMetric
ContextualPrecisionMetric
ContextualRecallMetric

Optionally:
GEval

Do not use GEval for deterministic business decisions where exact tests are better.

DeepEval should focus primarily on:

generated answer quality
grounding
context usage
regression

============================================================
25. DETERMINISTIC DECISION EVALUATION
============================================================

Do NOT use an LLM judge for:

amount comparisons
receipt checks
decision enums
variance

Use exact assertions.

Example:

input:
hotel amount=6500
limit=7000

expected:
COMPLIANT

input:
hotel amount=9500
limit=7000

expected:
NEEDS_REVIEW

Metric:

decision_accuracy =
correct decisions / total cases

Target should be 100% for deterministic golden cases.

============================================================
26. RAG BENCHMARK
============================================================

Benchmark at least:

A. vector-only

B. hybrid:
FTS + vector + RRF

C. hybrid + rerank

Use same golden retrieval dataset.

Compare:

Precision@5
Recall@10
MRR if available
latency

Generate a simple report.

Goal:

prove whether hybrid retrieval and reranking improve quality.

Do not assume they improve results without measurement.

============================================================
27. BENCHMARK IMPLEMENTATION
============================================================

Suggested:

evaluation/
    datasets/
    runners/
        evaluate_retrieval.py
        evaluate_rag.py
        evaluate_decisions.py
        benchmark_retrieval.py
    reports/

If repository already uses:

evaluation/ragas/
evaluation/deepeval/

preserve that structure.

============================================================
28. EVALUATION REPORTS
============================================================

Generate machine-readable and human-readable reports.

Suggested:

evaluation/reports/
    retrieval_metrics.json
    ragas_report.json
    deepeval_report.json
    decision_metrics.json
    retrieval_benchmark.json

Optional:
summary.md

Do not commit secrets or raw sensitive telemetry.

============================================================
29. THRESHOLDS
============================================================

Use configuration-driven thresholds.

Suggested initial POC thresholds:

Precision@5 >= 0.80

Recall@10 >= 0.90

Citation correctness >= 0.95

Deterministic decision accuracy = 1.00

For Ragas/DeepEval:
establish baseline first.

Do not invent arbitrary permanent quality thresholds.

If source OpenSpec already contains thresholds:
use them.

============================================================
30. BASELINE FIRST
============================================================

For Ragas/DeepEval:

first produce baseline scores.

Then define regression thresholds based on baseline and project expectations.

Do not fail CI immediately based on undocumented external metric thresholds.

============================================================
31. CI EVALUATION
============================================================

Create or update:

.github/workflows/rag-evaluation.yml

Expected behavior:

PR/push
    ->
install dependencies
    ->
run deterministic tests
    ->
run retrieval golden-set smoke evaluation
    ->
generate report
    ->
fail if deterministic retrieval thresholds regress

Avoid expensive live model evaluations for every CI run.

CI should use:

mocks
recorded fixtures
or controlled optional secrets

where appropriate.

============================================================
32. LIVE VS OFFLINE EVALUATION
============================================================

Separate:

FAST CI EVALUATION

from:

MANUAL / SCHEDULED MODEL EVALUATION

Fast CI:
- retrieval metrics
- citation correctness
- deterministic decisions
- mocked gateway

Manual/scheduled:
- Ragas
- DeepEval
- live model scoring if credentials available

Do not make every PR require expensive live LLM calls.

============================================================
33. LANGSMITH DATASETS / EXPERIMENTS
============================================================

If straightforward with installed LangSmith SDK:

optionally create or sync golden cases into LangSmith datasets.

Do not make this mandatory if it overcomplicates the POC.

The local JSON golden dataset remains authoritative for reproducible CI.

============================================================
34. MODEL GATEWAY TRACE LINKAGE
============================================================

Ensure Phase 006 Model Gateway sends trace metadata:

task
model
provider
prompt_version
input_tokens
output_tokens
retry_count
validation_retry_count
fallback_used

Correlate them with:

request_id
thread_id

============================================================
35. RETRIEVAL TRACE LINKAGE
============================================================

For each model call that uses RAG:

trace should make it possible to answer:

Which chunks were retrieved?

Which chunks came from lexical search?

Which came from vector search?

What was the RRF ranking?

What did reranker select?

Which chunks were sent to model?

Which chunks were cited?

============================================================
36. END-TO-END DEBUGGING GOAL
============================================================

An engineer should be able to answer:

"Why did this answer say INR 7000?"

by following one trace:

request
    ->
retrieval
    ->
POL-002 chunk
    ->
reranked evidence
    ->
Model Gateway
    ->
structured result
    ->
citation validator
    ->
final answer

Likewise:

"Why was this expense NEEDS_REVIEW?"

trace should show:

amount=9500
policy_limit=7000
deterministic comparison
decision=NEEDS_REVIEW

============================================================
37. NO BUSINESS LOGIC INSIDE OBSERVABILITY
============================================================

Observability code must never determine:

COMPLIANT
NON_COMPLIANT
NEEDS_REVIEW
APPROVE
REJECT

Tracing observes decisions.

It does not make decisions.

============================================================
38. TESTING OBSERVABILITY CODE
============================================================

Add unit tests for:

- trace metadata sanitization
- correlation metadata
- tracing disabled behavior
- tracing enabled mock behavior
- sensitive field redaction
- error category mapping

Do not require LangSmith network connectivity during tests.

Mock SDK interactions.

============================================================
39. RAGAS TESTING
============================================================

Create a small smoke evaluator.

Verify:

- dataset conversion works;
- required fields exist;
- evaluator can run when credentials are configured;
- evaluator can be skipped gracefully when model credentials are absent.

No CI failure merely because external evaluator credentials are missing unless job is explicitly configured as live evaluation.

============================================================
40. DEEPEVAL TESTING
============================================================

Create a small evaluation smoke path.

Validate dataset/test-case conversion.

Use installed DeepEval API.

Do not assume APIs from older tutorials.

If DeepEval requires an evaluator model/key:
support configuration via environment variables.

============================================================
41. CONFIGURATION
============================================================

Update config safely.

Possible settings:

LANGSMITH_TRACING
LANGSMITH_API_KEY
LANGSMITH_PROJECT

ENABLE_AI_EVALUATION

EVAL_DATASET_PATH

EVAL_PRECISION_AT_5_MIN
EVAL_RECALL_AT_10_MIN
EVAL_CITATION_CORRECTNESS_MIN

Do not put secrets in source.

============================================================
42. README / DOCUMENTATION
============================================================

Add documentation for:

Install:

python -m pip install langsmith ragas deepeval

LangSmith setup:

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=policyflow-ai-dev

How to run:

pytest

retrieval evaluation

Ragas evaluation

DeepEval evaluation

benchmark

Explain which commands require external model credentials.

============================================================
43. COMMANDS / SCRIPTS
============================================================

Prefer simple commands.

Examples:

python -m pytest backend/tests -v

python evaluation/runners/evaluate_retrieval.py

python evaluation/runners/evaluate_decisions.py

python evaluation/runners/evaluate_rag.py

python evaluation/runners/benchmark_retrieval.py

Adapt paths to actual repository.

Do not invent scripts if equivalent ones already exist.

============================================================
44. PERFORMANCE CONSIDERATIONS
============================================================

Tracing must not materially alter business behavior.

Avoid:

- uploading huge policy text;
- synchronous external evaluation during user requests;
- running Ragas per API call;
- running DeepEval per API call.

Runtime path:
trace only.

Evaluation:
offline.

============================================================
45. FAILURE BEHAVIOR
============================================================

If LangSmith is unavailable:

application should continue if tracing is optional.

Record local structured logs where possible.

Do not fail expense processing because observability backend is down.

If Ragas/DeepEval fails:

evaluation command fails/report shows error.

Production API remains unaffected.

============================================================
46. ARCHITECTURAL BOUNDARY
============================================================

Required structure after Phase 007:

                  PolicyFlow Runtime
                         |
      +------------------+------------------+
      |                                     |
   Business Flow                          Trace Hooks
      |                                     |
   LangGraph                             LangSmith
      |
      +--> Hybrid RAG
      +--> Model Gateway
      +--> Rules
      +--> HITL


                  Offline Quality
                         |
                  Golden Dataset
                         |
           +-------------+-------------+
           |             |             |
        Pytest         Ragas        DeepEval
           |
   Deterministic Checks

============================================================
47. REQUIRED RETRIEVAL BENCHMARK
============================================================

Use identical queries for:

vector-only
hybrid
hybrid+reranking

Produce results such as:

strategy
precision@5
recall@10
mrr
average_latency_ms

Do not alter production retrieval configuration during benchmark.

Use evaluator-specific configuration.

============================================================
48. IMPLEMENTATION ORDER
============================================================

Implement incrementally:

Step 1
Inspect current observability/evaluation code.

Step 2
Inspect/create OpenSpec 007 artifacts.

Step 3
Validate OpenSpec.

Step 4
Add dependencies:
langsmith
ragas
deepeval

Step 5
Add safe configuration.

Step 6
Implement LangSmith initialization.

Step 7
Implement trace context/correlation.

Step 8
Instrument LangGraph high-value nodes.

Step 9
Instrument retrieval.

Step 10
Instrument Model Gateway.

Step 11
Instrument deterministic decision metadata.

Step 12
Instrument citation validation.

Step 13
Instrument HITL interrupt/resume.

Step 14
Implement telemetry redaction.

Step 15
Finalize golden policy-QA dataset.

Step 16
Finalize expense decision dataset.

Step 17
Implement deterministic retrieval metrics.

Step 18
Implement citation correctness.

Step 19
Implement decision accuracy.

Step 20
Implement Ragas runner.

Step 21
Implement DeepEval runner.

Step 22
Implement vector-only vs hybrid vs reranked benchmark.

Step 23
Generate reports.

Step 24
Add observability tests.

Step 25
Add evaluation tests.

Step 26
Add/update GitHub Actions evaluation workflow.

Step 27
Run targeted tests.

Step 28
Run full backend tests.

Step 29
Run frontend build for regression validation.

Step 30
Run retrieval evaluation.

Step 31
Run deterministic decision evaluation.

Step 32
Run Ragas/DeepEval if credentials available.

Step 33
Validate OpenSpec.

Step 34
Update tasks.md accurately.

STOP.

Do not begin Phase 008.

============================================================
49. REQUIRED VALIDATION COMMANDS
============================================================

Use actual repository tooling.

Install:

python -m pip install langsmith ragas deepeval

Verify:

python -m pip show langsmith
python -m pip show ragas
python -m pip show deepeval

Backend:

python -m pytest -v

or:

python -m pytest backend/tests -v

Frontend:

npm run build

OpenSpec:

openspec status
openspec validate

or locally supported equivalents.

Evaluation:

run discovered evaluation scripts.

If a command fails:

- show exact command;
- show exact error;
- fix if within scope;
- rerun.

============================================================
50. PHASE 007 ACCEPTANCE CRITERIA
============================================================

Phase 007 is complete only when:

[ ] OpenSpec proposal/design/spec/tasks validate

[ ] LangSmith SDK integrated

[ ] tracing is configurable

[ ] app works when LangSmith is disabled

[ ] request_id is traced

[ ] thread_id is traced

[ ] graph nodes expose useful traces

[ ] retrieval counts and chunk IDs traced

[ ] RRF/reranker metadata traced

[ ] Model Gateway token/model/prompt data traced

[ ] retry/fallback metadata traced

[ ] citation validation metadata traced

[ ] deterministic decision metadata traced

[ ] HITL interrupt/resume traced

[ ] sensitive fields are redacted/minimized

[ ] golden Policy Q&A dataset exists

[ ] golden expense dataset exists

[ ] Precision@5 implemented

[ ] Recall@10 implemented

[ ] citation correctness implemented

[ ] deterministic decision accuracy implemented

[ ] Ragas evaluation runner exists

[ ] DeepEval evaluation runner exists

[ ] vector-only benchmark exists

[ ] hybrid benchmark exists

[ ] hybrid+rerank benchmark exists

[ ] reports are generated

[ ] no Ragas evaluation runs synchronously on API path

[ ] no DeepEval evaluation runs synchronously on API path

[ ] no LangSmith outage breaks business functionality

[ ] tests pass without live LangSmith access

[ ] CI does not require expensive live LLM evaluation by default

[ ] frontend build passes

[ ] OpenSpec tasks match actual implementation state

============================================================
51. DEFINITION OF DONE EXAMPLE
============================================================

Example request:

"What is the domestic hotel limit?"

LangSmith trace should show:

request_id
thread_id

build_metadata_filters
    status=ACTIVE
    category=HOTEL

hybrid_retrieve
    lexical_count=...
    vector_count=...

RRF
    chunk scores

reranker
    top evidence

Model Gateway
    task=POLICY_QA
    provider=OpenAI
    model=...
    prompt_version=v1
    tokens=...
    latency=...

citation validator
    valid citations=1

final response
    policy=POL-002
    amount=7000

Offline golden evaluation should confirm:

expected policy:
POL-002

expected fact:
7000

retrieval:
Precision@5
Recall@10

RAG:
faithfulness
answer relevance

citation:
correct

============================================================
52. INTERVIEW-LEVEL SUCCESS CRITERIA
============================================================

After implementation, I should be able to explain:

"LangSmith is used for runtime observability across LangGraph, retrieval, and Model Gateway execution. Ragas and DeepEval run offline against golden datasets to measure RAG quality and detect regressions. Deterministic business decisions are validated with exact Pytest assertions rather than LLM judges."

The implementation should demonstrate this clearly.

============================================================
53. FINAL IMPLEMENTATION REPORT
============================================================

When finished, provide:

1. OpenSpec files created/modified
2. dependencies added
3. LangSmith configuration
4. tracing modules added/modified
5. graph instrumentation
6. retrieval instrumentation
7. Model Gateway instrumentation
8. decision/citation instrumentation
9. redaction behavior
10. golden datasets created/updated
11. Ragas implementation
12. DeepEval implementation
13. deterministic metrics
14. retrieval benchmark
15. evaluation reports
16. GitHub Actions changes
17. tests created
18. commands executed
19. backend test results
20. frontend build result
21. retrieval evaluation results
22. Ragas results if executed
23. DeepEval results if executed
24. OpenSpec validation result
25. known limitations
26. items deferred to Phase 008
27. concise end-to-end observability/evaluation architecture

Do not merely say:
"Phase 007 implemented."

Show actual results and evidence.

STOP after Phase 007.

Do not begin 008-aws-deployment-hardening automatically.

============================================================
53. Files Updated during this Phase
============================================================
Generated local reports:

- evaluation/reports/retrieval_evaluation.json
- evaluation/reports/citation_evaluation.json
- evaluation/reports/expense_decisions.json
- evaluation/reports/retrieval_benchmark.json
- evaluation/reports/ragas.json
- evaluation/reports/deepeval.json
- evaluation/reports/SUMMARY.md

These timestamped/latency-bearing reports are ignored build artifacts, not source
files.

## Actual local results

Docker evidence:

- PostgreSQL and Redis healthy
- Alembic head 20260920_0004
- 6 ACTIVE documents and 50 chunks

Deterministic evaluation:

- hybrid Precision@5: 0.9090909091
- hybrid Recall@10: 0.9090909091
- hybrid MRR: 0.9090909091
- citation correctness: 1.0
- valid-citation coverage: 1.0
- deterministic decision accuracy: 1.0

Benchmark:

| Strategy | Precision@5 | Recall@10 | MRR | Average latency |
|---|---:|---:|---:|---:|
| vector | 0.9091 | 0.9091 | 0.9091 | 185.26 ms |
| hybrid | 0.9091 | 0.9091 | 0.9091 | 50.52 ms |
| hybrid+rerank | 0.9091 | 0.9091 | 0.9091 | 58.23 ms |

The hybrid and vector quality scores tied in this local run; hybrid was faster.
The hybrid+rerank arm used the deliberately unavailable evaluator reranker and is
correctly labeled fallback. No genuine reranker improvement is claimed.

Ragas and DeepEval recorded SKIP because live external evaluation was disabled.
No score or threshold was invented.

Regression evidence:

- focused Phase 007 and Policy Q&A: 44 passed
- complete backend: 116 passed
- frontend: 2 tests passed
- Vite production build: passed
- workflow YAML parse: passed
- OpenSpec change validation: valid
- canonical OpenSpec validation: 6 passed, 0 failed
- all OpenSpec validation: 7 passed, 0 failed
- credential-signature audit: clean
- runtime evaluator-import audit: clean
- direct OpenAI SDK audit: adapter only
- git diff whitespace audit: no errors; line-ending notices only

## CI

The RAG evaluation workflow now runs credential-free dataset, metric, tracing,
decision, optional-evaluator-skip, report, and benchmark-smoke checks for pull
requests and main-branch pushes. It uploads report artifacts. A separate guarded
workflow-dispatch job references the optional external evaluator secret; default
jobs do not.

## Files created for Phase 007

- backend/app/observability/context.py
- backend/app/observability/contracts.py
- backend/app/observability/redaction.py
- backend/tests/test_observability.py
- backend/tests/test_evaluation.py
- evaluation/__init__.py
- evaluation/models.py
- evaluation/metrics.py
- evaluation/reporting.py
- evaluation/retrieval.py
- evaluation/run_retrieval.py
- evaluation/run_decisions.py
- evaluation/benchmark.py
- evaluation/summarize.py
- docs/phase-007-implementation-report.md
- openspec/changes/007-observability-evaluation/proposal.md
- openspec/changes/007-observability-evaluation/design.md
- openspec/changes/007-observability-evaluation/specs/observability-evaluation/spec.md
- openspec/changes/007-observability-evaluation/tasks.md

## Files updated for Phase 007

- .github/workflows/rag-evaluation.yml
- README.md
- backend/requirements.txt
- backend/app/core/config.py
- backend/app/graph/graph.py
- backend/app/graph/expense_graph.py
- backend/app/observability/tracing.py
- backend/app/observability/metrics.py
- backend/app/services/policy_service.py
- backend/app/services/expense_service.py
- backend/app/services/exception_service.py
- backend/tests/test_policy_qa.py
- evaluation/datasets/policy_qa_golden.json
- evaluation/datasets/expense_cases.json
- evaluation/ragas/evaluate_rag.py
- evaluation/deepeval/evaluate_agent.py
- docs/local-validation.md
- local ignored .env.example placeholder template

## Known limitations and Phase 008 deferrals

- Live LangSmith visual verification requires an operator-owned key and was not
  performed during credential-free validation.
- Ragas/DeepEval paid baselines require explicit enablement, credentials, and a
  generated answer/context bundle.
- Genuine reranker benchmarking requires an explicitly configured local BGE or
  authorized Cohere evaluator.
- AWS/CloudWatch, Prometheus/Grafana, production dashboards/alerts, durable cost
  accounting, new retrieval systems, and deployment hardening remain deferred.