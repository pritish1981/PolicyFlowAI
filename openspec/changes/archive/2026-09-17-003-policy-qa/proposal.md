## Why

PolicyFlow AI can retrieve and validate policy evidence, but it cannot yet answer an employee's natural-language policy question. Phase 003 adds the bounded, evidence-grounded Q&A use case required by FRD v1.0 while keeping policy thresholds, source identity, eligibility, and citation acceptance under deterministic application control.

## What Changes

- Replace the Phase 002 evidence-only policy query contract with `POST /api/v1/policy/query` request and response models for a grounded answer, verified citations, request correlation, and controlled evidence status.
- Add a Policy Q&A application service and a minimal `policy_qa` LangGraph path that validates input, constructs deterministic eligibility filters, reuses hybrid PostgreSQL retrieval/RRF/reranking, invokes the central Model Gateway, validates citations, and produces a final response.
- Add the smallest provider-neutral Model Gateway contract and OpenAI adapter needed for structured Policy Q&A generation, including bounded retries/timeouts, token controls, and model metadata. Tests use injected fakes and require no provider credentials.
- Construct citation excerpts only from stored, eligible chunks and return `INSUFFICIENT_INFORMATION` whenever evidence or model citations cannot support the answer.
- Add a focused React Policy Q&A screen with input, loading/error/abstention states, and citation presentation.
- Expand the deterministic Policy Q&A golden dataset and add unit, service, API integration, graph, and frontend build coverage.
- Add sanitized structured logging for request, retrieval, reranking, model, citation, and evidence-status metadata.
- Keep expense assessment, compliance decisions, exceptions, human review, interrupt/resume, full evaluation suites, and deployment work out of scope.

## Capabilities

### New Capabilities

- `policy-qa`: Natural-language expense-policy questions answered only from eligible, reranked policy evidence through a governed model call and deterministic citation validation, with safe abstention and a React presentation flow.

### Modified Capabilities

None. Phase 003 consumes the existing `policy-ingestion-and-hybrid-rag` capability without changing its ingestion, retrieval, fusion, reranking, or evidence-validation requirements.

## Impact

- **API and schemas:** `backend/app/api/`, `backend/app/schemas/`, request correlation, response/error contracts, and router registration.
- **Application and workflow:** `backend/app/services/`, `backend/app/graph/`, and Policy Q&A state/nodes/edges.
- **RAG and gateway:** integration with existing PostgreSQL FTS, pgvector, RRF, reranking, and citation code; new minimal structured Model Gateway path under `backend/app/gateway/`.
- **Configuration and observability:** environment-driven model/retrieval settings and sanitized structured telemetry; no secrets or new persistence technology.
- **Frontend:** typed API client plus Policy Q&A page/components under `frontend/src/`.
- **Verification:** backend unit/service/integration tests, deterministic golden data, frontend production build, and strict OpenSpec validation.
- **Database:** no schema or migration change is expected; Phase 003 reuses the Phase 002 policy document and chunk tables and indexes.
