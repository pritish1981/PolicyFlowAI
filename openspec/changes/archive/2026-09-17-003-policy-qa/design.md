## Context

See `proposal.md` for motivation and `specs/policy-qa/spec.md` for the behavioral contract. Phase 002 already provides versioned ACTIVE policy documents/chunks, PostgreSQL FTS and pgvector queries, deterministic eligibility predicates, RRF, Cohere/BGE adapters, and authoritative citation lookup. Its current `/api/v1/policy/query` route returns evidence only, while the Phase 003 schema, service, graph, gateway, and frontend modules are placeholders. The React application currently presents platform health only.

The FRD is authoritative and defines the operating order as retrieve evidence, interpret policy, validate citations, and abstain when evidence is insufficient. The HLD/LLD assign HTTP concerns to routers, use-case coordination to services, orchestration to LangGraph, persistence/querying to repositories/RAG, and all provider calls to a central Model Gateway. Phase 003 must preserve those boundaries without implementing later expense-decision or HITL paths.

## Goals / Non-Goals

**Goals:**

- Deliver one complete Policy Q&A vertical slice from React through FastAPI, service, LangGraph, Phase 002 RAG, Model Gateway, deterministic citation validation, and response mapping.
- Keep authoritative eligibility, source identity, citation excerpts, and abstention decisions deterministic.
- Make all provider-dependent components injectable so unit and CI integration tests need no OpenAI or Cohere credentials.
- Retain Phase 002 query/index behavior and database schema while enriching retrieval hit metadata needed for observability.
- Expose bounded, sanitized operational metadata for each stage.

**Non-Goals:**

- Expense submission or COMPLIANT/NON_COMPLIANT/NEEDS_REVIEW computation.
- Exception creation, approval, reviewer UI, or LangGraph interrupt/resume.
- A general multi-scenario production graph, durable graph checkpoints, full Ragas/DeepEval, or LangWatch dashboards.
- Database migrations, new vector stores, deployment changes, or autonomous policy decisions.

## Decisions

### 1. Replace the evidence-only route with a thin versioned API adapter

`backend/app/api/routes/policies.py` will own `POST /api/v1/policy/query`, use strict Pydantic request/response models from `backend/app/schemas/policy.py`, accept or create a request ID, call `PolicyService`, and map known domain errors. `main.py` will register this router instead of the Phase 002 evidence-only `app.api.v1.policy` router. The old module may remain as a compatibility shim only if existing tests/imports require it; two independently implemented handlers will not coexist.

The request uses `question`, optional `category`, and optional `region`. Unknown fields are forbidden. Question normalization occurs in Pydantic and is repeated defensively at the graph boundary. The response uses `GROUNDED` and `INSUFFICIENT_INFORMATION` only.

Alternative considered: extend the Phase 002 route in place. Rejected because it currently performs database/RAG/citation work directly in the router, contrary to the LLD boundary and requested service/graph design.

### 2. Keep one Phase 003 graph with explicit node boundaries

A typed `PolicyQAState` will contain only Phase 003 fields while retaining LLD-compatible names: request/thread IDs, scenario, user query, assessment date, metadata filters, lexical/vector/fused/reranked hits, answer, citation IDs/citations, evidence status, model usage, and sanitized errors. The compiled graph follows:

`START -> validate_request -> set_policy_qa -> build_metadata_filters -> hybrid_retrieve -> fuse_results -> rerank_results -> generate_grounded_answer -> validate_citations -> final_response -> END`

No expense or human-review branches are added. Nodes receive dependencies through a workflow factory/context rather than importing concrete external clients, allowing deterministic node and service tests.

Alternative considered: keep orchestration entirely in `PolicyService`. Rejected because the FRD/LLD explicitly require a Policy Q&A LangGraph path and later phases need compatible graph state names.

### 3. Refactor Phase 002 retrieval composition without replacing its SQL

The current Phase 002 `search()` embeds, runs both searches, and fuses internally. Phase 003 needs lexical, vector, and fused counts/ranks as distinct graph state. The existing PostgreSQL SQL functions remain authoritative; a small orchestration API will expose first-stage results and fusion while preserving `search()` for compatibility.

`SearchHit` will carry separate optional `lexical_rank`, `vector_rank`, `rrf_score`, and `rerank_score` fields rather than overloading one `score`. Fusion deduplicates by `chunk_id`, contributes `1/(60+rank)` for each list, preserves both source ranks, and orders by descending score with a stable chunk-ID tie break. The configured first-stage top N defaults to 20; fused candidates passed to reranking remain bounded; final evidence defaults to 5.

Metadata filters always include ACTIVE and the effective interval. The public `category` input maps deterministically to the existing policy `domain`. Region permits the exact region and GLOBAL as established in Phase 002. Omitted optional inputs add no restrictive predicate. The model never builds or alters filters.

Alternative considered: call the existing monolithic `search()` from a single graph node. Rejected because it cannot truthfully populate or trace the required stage-specific state.

### 4. Inject a reranker and make fallback explicit

The graph depends on the existing `Reranker` protocol through a resolver/factory. Cohere remains primary; BGE remains the optional adapter. Tests inject a deterministic fake. A configuration value controls whether a provider failure falls back to RRF order; fallback is logged. When disabled, reranker failure becomes a safe service failure rather than silently changing ranking behavior.

Provider calls remain inside adapters and never inside graph nodes. This keeps the current Phase 002 abstraction and avoids a new dependency architecture.

### 5. Add the smallest structured Model Gateway contract needed now

The gateway defines `ModelTask.POLICY_QA`, request context, usage/result metadata, a provider adapter protocol, task routing, timeout, bounded retry behavior for transient failures, input/output token limits, and `invoke_structured`. The OpenAI adapter is the only Phase 003 provider implementation and is instantiated only when configured. It is not called directly by API, service, graph, RAG, or citation code.

`GroundedPolicyAnswer` is a strict Pydantic model with a non-empty answer, UUID citation IDs, and `insufficient_information`. The evidence-only system prompt forbids external knowledge, invented thresholds/source metadata, compliance decisions, and exception approval. The model receives numbered/ID-labelled top chunks and returns chunk IDs only; it never authors excerpts.

Gateway unavailability after bounded retry raises a typed retryable domain error mapped to HTTP 503. Invalid structured output is retried at most once according to gateway configuration and is never returned raw.

Alternative considered: direct OpenAI SDK use in the generation node. Rejected because it violates FR-17 and would couple provider concerns to orchestration.

### 6. Make citation acceptance and final status deterministic

The model's cited IDs are intersected with the actual reranked set before database validation. The validator reloads authoritative chunk/document rows and verifies ACTIVE status, effective/expiry dates, policy code, version, section ID/title, and content identity. It creates a bounded excerpt from stored content. Model-provided excerpts or metadata are not accepted.

The final response is `GROUNDED` only when the model did not declare insufficiency, the answer is material, and at least one citation is valid. No hits, model insufficiency, or zero valid citations yields the fixed safe message: `I could not find enough verified policy evidence to answer this question reliably.` and an empty citation list. Retrieval/database failures are not converted into abstention because that would pretend a successful evidence search; they propagate as service errors.

Alternative considered: partially return an answer after dropping invalid citations. Rejected because it could leave material claims unsupported.

### 7. Keep PolicyService as the use-case boundary

`PolicyService` creates request/thread context, fixes the assessment date at request start, invokes the compiled workflow, converts final graph state to the API schema, and enforces the final invariant. It accepts factories/dependencies for retrieval, reranking, gateway, sessions, clock, and IDs to keep tests deterministic. The router performs no SQL, RAG, or model work.

### 8. Extend the existing frontend shell instead of adding routing infrastructure

The current application has no router. Phase 003 will add `policyApi.ts`, `PolicyQuestion`, `CitationPanel`, and `PolicyQAPage`, and compose the page into `App.tsx` alongside a compact platform-status section. This avoids introducing React Router for a single new view. Typed models mirror the API; client-side length checks improve feedback but do not replace backend validation.

### 9. Use structured logs as the Phase 003 observability hook

Existing logging configuration will be reused. Stage logs include request ID, `scenario=policy_qa`, sanitized filter values, candidate counts/IDs, rank scores, citation count, provider/model/latency/token metadata when available, fallback flags, and final evidence status. Raw prompts, keys, connection strings, full documents, and unnecessary query content are excluded.

### 10. Verify behavior in layers with no live model dependency

Unit tests cover request and structured-output schemas, filters, RRF, and citation validation. Service/graph tests inject retrieval, reranker, gateway, and repository/session fakes for grounded, abstention, citation mismatch, reranker fallback, and gateway failure paths. API tests override the service dependency and assert 200/422/503 contracts. Existing live PostgreSQL tests continue to verify actual FTS, pgvector, indexes, eligibility, and the hotel POL-002 corpus. The golden JSON expands to 8-12 deterministic queries for smoke evaluation only. Frontend verification is the TypeScript/Vite production build because no frontend test runner currently exists.

## Risks / Trade-offs

- **The current RAG hit type overloads a single score** -> Extend it compatibly with explicit ranks and retain transitional access only where existing Phase 002 tests need it.
- **Local embedding or BGE models may require downloads** -> Keep adapters lazy and inject deterministic fakes in CI; live PostgreSQL/model validation remains an explicit local smoke step.
- **Cohere/OpenAI credentials may be absent** -> Do not initialize providers during import; fail with a typed 503 at runtime and keep all automated tests credential-free.
- **A permissive RRF fallback changes relevance quality** -> Make fallback configuration explicit, bound it to fused candidates, and expose it in telemetry.
- **A model may cite one chunk while making multiple unsupported claims** -> Use a restrictive prompt and fail closed on invalid/zero citations; full claim-level entailment evaluation is deferred to the evaluation phase.
- **Replacing the Phase 002 response is an API evolution** -> Treat Phase 002 evidence-only behavior as internal/reusable RAG functionality and update repository tests/docs in the same bounded change.
- **PostgreSQL availability is required for truthful retrieval** -> Propagate retrieval failures; never turn infrastructure failure into `INSUFFICIENT_INFORMATION`.

## Migration Plan

1. Add schemas, gateway contracts, graph state/nodes, service, and tests while retaining Phase 002 retrieval APIs.
2. Extend retrieval hit metadata and split orchestration stages with compatibility coverage for existing Phase 002 tests.
3. Register the new thin route and remove the old handler registration after API tests pass.
4. Add the frontend view and typed client; run the production build.
5. Run unit/service/API suites, then live PostgreSQL integration and corpus smoke checks when the configured database is available.
6. Run strict OpenSpec validation and mark only verified tasks complete.

Rollback restores the old evidence-only router registration and frontend shell; no database downgrade is required because Phase 003 adds no migration.
