## 1. Contracts and configuration

- [x] 1.1 Implement strict Policy Q&A request, response, citation, evidence-status, and grounded-model Pydantic schemas; verify unit tests cover trimming, 3/2000-character bounds, forbidden fields, UUID citation IDs, and insufficient-information output.
- [x] 1.2 Add environment-driven Policy Q&A gateway, timeout/retry/token, citation-required, reranker-fallback, retrieval, and top-K settings without hardcoded credentials; verify configuration tests and `.env.example` document non-secret values.
- [x] 1.3 Add typed domain errors for model unavailability, invalid structured output, reranker failure, and retrieval failure; verify router/service error-mapping tests cover HTTP 503 versus safe abstention.

## 2. Deterministic retrieval and citation controls

- [x] 2.1 Implement a deterministic Policy Q&A metadata-filter builder that always applies ACTIVE and effective/expiry constraints and optionally maps category and region; verify unit tests cover required and omitted filters.
- [x] 2.2 Extend hybrid retrieval orchestration to expose lexical and vector top-20 lists separately while preserving the existing PostgreSQL FTS, pgvector, and compatibility search path; verify unit tests and existing Phase 002 integration tests pass.
- [x] 2.3 Extend RRF hit metadata to preserve lexical rank, vector rank, RRF score, and stable chunk-ID deduplication; verify tests cover lexical-only, vector-only, common, duplicate, tie, and ordering cases with k=60.
- [x] 2.4 Resolve the existing reranker through its interface, return configured top 3-5 evidence chunks, and implement explicit configured RRF fallback behavior; verify fake-reranker tests cover success, fallback, and fail-closed modes without credentials.
- [x] 2.5 Harden deterministic citation validation to accept only model-selected IDs from reranked evidence, recheck stored eligibility and exact metadata, and create bounded excerpts server-side; verify tests cover valid, unknown, inactive, expired, metadata-mismatch, and zero-valid-citation cases.

## 3. Model Gateway and grounded generation

- [x] 3.1 Implement `ModelTask.POLICY_QA`, gateway/provider protocols, model context/result metadata, routing, token controls, timeouts, bounded transient retry, and structured Pydantic validation; verify gateway contract tests use fake providers for valid, invalid, retry, and unavailable results.
- [x] 3.2 Implement the lazy OpenAI structured-output adapter behind the provider protocol with configuration-only secrets; verify adapter tests mock the SDK and source scans find no direct provider calls outside `backend/app/gateway/`.
- [x] 3.3 Implement the versioned evidence-only Policy Q&A prompt/context builder that sends exact chunk IDs and forbids invented facts, compliance decisions, exception approvals, and external knowledge; verify prompt tests assert all grounding rules and selected evidence fields.

## 4. Policy Q&A workflow and service

- [x] 4.1 Implement the Phase 003 `PolicyQAState` and explicit LangGraph nodes for validation, scenario assignment, filter building, retrieval, fusion, reranking, generation, citation validation, and final response; verify graph tests assert grounded and no-evidence paths and confirm no expense/HITL branch exists.
- [x] 4.2 Compile the minimal Policy Q&A graph with injectable retrieval, reranker, gateway, session, clock, and ID dependencies; verify a graph integration test records the expected node order and uses no live credentials.
- [x] 4.3 Implement `PolicyService` to create request context, invoke the graph, map state to the response schema, and enforce GROUNDED/citation invariants; verify service tests cover grounded POL-002 output, insufficient evidence, citation rejection, gateway failure, and retrieval failure.
- [x] 4.4 Add sanitized structured stage logging for request IDs, filters, candidate counts/IDs/ranks, fallback, model metadata, citation count, and evidence status; verify log-capture tests assert required fields and absence of prompts, document bodies, keys, and connection strings.

## 5. FastAPI delivery

- [x] 5.1 Implement the thin `POST /api/v1/policy/query` router with request-ID propagation/generation, service dependency injection, and known error mapping; verify API tests cover grounded 200, abstention 200, validation 422, model 503, and unsupported fields.
- [x] 5.2 Register the Phase 003 router in `main.py` and retire or shim the Phase 002 evidence-only handler without duplicate routes; verify OpenAPI exposes exactly one operation for `/api/v1/policy/query` and existing health/admin tests pass.
- [x] 5.3 Add a credential-free API integration test whose injected retrieval/reranker/gateway path returns a domestic hotel answer cited to POL-002, plus a no-evidence abstention case; verify both run in the normal backend test suite.

## 6. React Policy Q&A experience

- [x] 6.1 Add typed Policy Q&A client models and `policyApi.ts` for the POST contract with abort/error handling; verify TypeScript compilation catches contract drift and the frontend production build passes.
- [x] 6.2 Implement `PolicyQuestion` with the example hotel question, input validation, submit control, and loading/disabled behavior; verify accessible labels, validation messaging, and keyboard submission in component behavior or build-time checks available in the repository.
- [x] 6.3 Implement `CitationPanel` and `PolicyQAPage` to display grounded answers, evidence status, citations, API errors, and insufficient-information state; verify the page never renders a threshold as grounded when citations are absent.
- [x] 6.4 Integrate Policy Q&A into the existing responsive application shell without adding expense or reviewer screens; verify `npm.cmd run build` succeeds and manual local inspection covers desktop and narrow layouts.

## 7. Golden data and full validation

- [x] 7.1 Populate `evaluation/datasets/policy_qa_golden.json` with 8-12 deterministic Phase 003 questions covering POL-002 through POL-006 facts and abstention; verify a dataset schema/smoke test validates expected policy codes, facts, and unique IDs.
- [x] 7.2 Run targeted unit, service, graph, and API tests, fix in-scope failures, and record exact commands/results; verify all Phase 003 tests pass without OpenAI or Cohere credentials.
- [x] 7.3 Run the full backend test suite and live PostgreSQL migration/hybrid-retrieval smoke when the configured database is available; verify the migration remains at the Phase 002 head and the hotel query retrieves active POL-002 evidence.
- [x] 7.4 Run the frontend production build and any configured frontend tests; verify artifacts compile successfully and report explicitly that no test runner exists if `package.json` still defines none.
- [x] 7.5 Run strict OpenSpec validation for `003-policy-qa` and the supported all/spec scopes, fix Phase 003 validation errors, then mark only completed tasks checked and verify OpenSpec reports implementation-ready or complete status truthfully.
