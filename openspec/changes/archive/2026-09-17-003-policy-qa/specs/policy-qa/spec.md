## Purpose

Provides employees with natural-language expense-policy answers grounded only in eligible, reranked policy evidence, with verified citations and safe abstention when support is insufficient.

## ADDED Requirements

### Requirement: Validated policy question contract
The system SHALL expose `POST /api/v1/policy/query` with a required trimmed question between 3 and 2000 characters, optional category and region filters, a generated or propagated request identifier, and rejection of unsupported request fields.

#### Scenario: Valid question
- **WHEN** a caller submits a supported question and optional metadata filters
- **THEN** the system accepts the request and returns a response containing `request_id`, `answer`, `citations`, and a controlled `evidence_status`

#### Scenario: Invalid question
- **WHEN** the question is blank after trimming, shorter than 3 characters, longer than 2000 characters, or the request contains unsupported fields
- **THEN** the system returns HTTP 422 without invoking retrieval or a model

### Requirement: Deterministic evidence eligibility
The system SHALL always restrict Policy Q&A evidence to ACTIVE documents effective on the assessment date and not expired on that date, and SHALL apply supplied category and region filters deterministically without allowing a model to alter eligibility.

#### Scenario: Eligible active policy
- **WHEN** an active policy is effective on the assessment date, is not expired, and matches the applicable supplied metadata
- **THEN** its chunks are eligible for retrieval

#### Scenario: Inactive or date-ineligible policy
- **WHEN** a policy is inactive, not yet effective, or expired on the assessment date
- **THEN** its chunks are excluded before generation regardless of model behavior

#### Scenario: Optional metadata omitted
- **WHEN** the caller omits category or region
- **THEN** the system does not introduce an unsupported restrictive value for that optional filter

### Requirement: Hybrid evidence selection
The system SHALL reuse PostgreSQL full-text and pgvector retrieval, deterministic Reciprocal Rank Fusion, chunk-ID deduplication, and the configured reranker to select no more than the configured top 3-5 evidence chunks for Policy Q&A.

#### Scenario: Evidence appears in both retrieval lists
- **WHEN** a chunk appears in lexical and semantic results
- **THEN** fusion combines its reciprocal-rank contributions once under its chunk ID and preserves source ranks for observability

#### Scenario: Evidence appears in one retrieval list
- **WHEN** a chunk appears in only one first-stage result list
- **THEN** fusion retains it with the contribution from that list and does not create a duplicate candidate

#### Scenario: Reranker unavailable with fallback enabled
- **WHEN** the configured reranker is unavailable and the configured safe fallback permits fused ordering
- **THEN** the system uses the highest fused candidates and records the fallback without inventing evidence

### Requirement: Governed structured generation
The system SHALL send only the normalized question and selected evidence chunks through the central Model Gateway using the `POLICY_QA` task, and SHALL require a validated structured result containing an answer, exact citation chunk IDs, and an insufficient-information flag.

#### Scenario: Grounded model result
- **WHEN** the provider returns a schema-valid answer whose material claims cite selected evidence
- **THEN** the gateway returns the structured result with provider, model, latency, and token metadata when available

#### Scenario: Invalid structured result
- **WHEN** provider output cannot be validated after the configured bounded retry or repair behavior
- **THEN** the system does not return the unvalidated text as a policy answer

#### Scenario: Model unavailable
- **WHEN** the gateway exhausts bounded transient retries and no configured fallback succeeds
- **THEN** the API returns HTTP 503 using the project error convention

### Requirement: Deterministic citation validation
The system SHALL accept a model citation only when its chunk ID belongs to the reranked evidence set and the authoritative stored chunk matches its policy code, version, section identity, ACTIVE status, and effective interval; citation excerpts SHALL be constructed server-side from stored content.

#### Scenario: Valid citation
- **WHEN** a cited chunk is in the reranked evidence set and its stored identity and eligibility are valid
- **THEN** the response citation contains the stored chunk ID, policy code, policy version, section ID, section title, and server-created excerpt

#### Scenario: Unknown or mismatched citation
- **WHEN** a cited chunk is absent from reranked evidence or its stored identity or eligibility does not match
- **THEN** the citation is rejected and no model-supplied source metadata or excerpt is trusted

### Requirement: Safe grounded answer or abstention
The system SHALL return `GROUNDED` only when a non-empty material answer has at least one valid citation, and SHALL otherwise return `INSUFFICIENT_INFORMATION` with a controlled safe message and no fabricated policy fact.

#### Scenario: Supported answer
- **WHEN** selected evidence supports the answer and at least one cited chunk passes deterministic validation
- **THEN** the response has `evidence_status` `GROUNDED`, the grounded answer, and verified citations

#### Scenario: No retrievable evidence
- **WHEN** hybrid retrieval produces no eligible evidence
- **THEN** the response has `evidence_status` `INSUFFICIENT_INFORMATION`, a safe abstention message, and no citations without invoking a provider unnecessarily

#### Scenario: Citations fail validation
- **WHEN** the model produces an answer but zero cited chunks pass deterministic validation
- **THEN** the model conclusion is discarded and the response safely abstains

#### Scenario: Model declares insufficient information
- **WHEN** the structured model result declares insufficient information
- **THEN** the response safely abstains even if retrieval returned candidates

### Requirement: Policy Q&A workflow boundary
The system SHALL orchestrate Policy Q&A as a single `policy_qa` workflow from deterministic request validation through filter construction, hybrid retrieval, fusion, reranking, grounded generation, citation validation, and final response, without making an expense-compliance or exception decision.

#### Scenario: Policy question execution
- **WHEN** a valid policy question is submitted
- **THEN** the workflow follows the Policy Q&A path and returns a grounded response or safe abstention

#### Scenario: No decision authority
- **WHEN** a question asks the Policy Q&A path to approve an expense or exception
- **THEN** the workflow does not emit COMPLIANT, NON_COMPLIANT, approval, or rejection outcomes

### Requirement: Policy Q&A user interface
The frontend SHALL provide a professional Policy Q&A view with question input, optional metadata inputs supported by the API, client validation, submit/loading/error states, evidence status, answer text, and verified citation details.

#### Scenario: Grounded answer display
- **WHEN** the API returns a GROUNDED response
- **THEN** the page displays the answer and each citation's policy code, version, section title, and excerpt

#### Scenario: Abstention display
- **WHEN** the API returns INSUFFICIENT_INFORMATION
- **THEN** the page displays the safe insufficient-evidence state without presenting a policy threshold as fact

### Requirement: Traceable and secret-safe operation
The system SHALL emit sanitized structured metadata sufficient to trace Policy Q&A API, workflow, retrieval, reranking, model, citation, and final evidence-status stages without logging secrets or entire policy documents.

#### Scenario: Completed request telemetry
- **WHEN** a Policy Q&A request completes
- **THEN** telemetry can correlate the request ID with scenario, applied filter names/values, candidate counts and IDs, available ranking scores, model metadata, valid citation count, and evidence status

#### Scenario: Sensitive configuration
- **WHEN** telemetry is emitted during provider or retrieval failure
- **THEN** API keys, database credentials, and full policy documents are absent from logs
