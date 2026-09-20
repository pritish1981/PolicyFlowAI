# Observability Evaluation Specification

## Purpose

Defines privacy-safe runtime traceability and reproducible offline quality evaluation for PolicyFlow AI without changing deterministic business authority or requiring external observability and evaluator services for normal operation.

## Requirements

### Requirement: Optional runtime tracing
The system SHALL support configurable runtime tracing and SHALL continue serving business workflows when tracing is disabled, credentials are absent, or the tracing backend is unavailable.

#### Scenario: Tracing disabled
- **WHEN** runtime tracing is disabled or no tracing credential is configured
- **THEN** Policy Q&A, expense assessment, and exception review continue with local structured logging and no external trace dependency

#### Scenario: Tracing backend unavailable
- **WHEN** an enabled tracing export fails
- **THEN** the failure does not change the API response, deterministic decision, persisted business state, checkpoint behavior, or human-review outcome

### Requirement: End-to-end correlation
The system SHALL propagate existing request and thread identifiers through traced workflow stages and SHALL include expense, exception, and review identifiers when those identifiers already exist.

#### Scenario: Correlated policy request
- **WHEN** a Policy Q&A request executes retrieval, generation, and citation validation
- **THEN** the relevant trace stages share the request and thread identifiers rather than generating unrelated correlation identifiers

#### Scenario: Correlated exception lifecycle
- **WHEN** an expense enters exception review and later resumes
- **THEN** trace metadata links the expense, exception, thread, and authorized review action without replacing business-table identity

### Requirement: Business-relevant workflow stage traces
The system SHALL trace major API, LangGraph, retrieval, fusion, reranking, Model Gateway, deterministic-validation, citation-validation, human-review, and finalization stages with stage name, scenario, duration, outcome, and normalized error category when applicable. It SHALL NOT export full graph state.

#### Scenario: Successful node execution
- **WHEN** a major workflow node completes
- **THEN** its trace records correlation metadata, stage identity, duration, and success without serializing the complete state

#### Scenario: Failed node execution
- **WHEN** a traced stage raises an error
- **THEN** its trace records a sanitized normalized category and failure outcome while the existing caller error contract remains authoritative

### Requirement: Retrieval trace metadata
The system SHALL expose metadata sufficient to reconstruct lexical, vector, reciprocal-rank-fusion, and reranking behavior using counts, chunk identifiers, ranks, scores, filters, selected evidence identifiers, and latency without exporting full policy content.

#### Scenario: Hybrid retrieval trace
- **WHEN** a hybrid retrieval request completes
- **THEN** telemetry identifies metadata filters, lexical and vector result counts, source ranks, fused results, RRF scores, reranked results, reranker scores, and selected chunk identifiers

#### Scenario: Retrieval failure
- **WHEN** retrieval or reranking fails or uses its configured fallback
- **THEN** telemetry identifies the safe failure or fallback category without exposing query text or document bodies unnecessarily

### Requirement: Governed model trace linkage
The system SHALL reuse Model Gateway metadata for task, provider, model, prompt version, available token counts, latency, transient retries, validation retries, fallback use, guardrail outcome, error category, request identifier, and thread identifier. Provider-specific tracing SHALL remain behind the gateway boundary.

#### Scenario: Successful governed generation
- **WHEN** a Model Gateway request succeeds
- **THEN** its trace contains the governed route and usage metadata and links to the surrounding workflow trace

#### Scenario: Governed generation failure
- **WHEN** the gateway returns a controlled timeout, rate-limit, validation, guardrail, or unavailability error
- **THEN** telemetry records the provider-neutral category without raw provider exceptions or payloads

### Requirement: Citation and decision trace metadata
The system SHALL trace citation counts and identifiers, deterministic validation outcomes, and expense decision metadata using safe values while keeping database-backed policy validation and deterministic rules authoritative.

#### Scenario: Citation validation result
- **WHEN** generated citations are validated
- **THEN** telemetry records generated, valid, and invalid counts, cited chunk identifiers, and categorized rejection reasons available from validation

#### Scenario: Deterministic expense result
- **WHEN** an expense assessment completes
- **THEN** telemetry records the expense identifier and type, applicable rule type, safe policy limit, decision, confidence, valid citation count, and abstention category without making or changing the decision

### Requirement: HITL lifecycle trace markers
The system SHALL emit trace markers for human-review interruption and workflow resumption using identifiers, review status, and action while excluding full reviewer comments and preserving human authority.

#### Scenario: Human review interrupted
- **WHEN** an exception workflow pauses for authorized review
- **THEN** telemetry records `HUMAN_REVIEW_INTERRUPTED` with thread and exception correlation metadata

#### Scenario: Workflow resumed
- **WHEN** an authorized review or additional-information action resumes the workflow
- **THEN** telemetry records `WORKFLOW_RESUMED`, the safe action category, and the existing identifiers without treating telemetry as business truth

### Requirement: Telemetry minimization and redaction
The system SHALL apply centralized allow-listing and redaction before external telemetry export and SHALL exclude credentials, authorization data, database connection secrets, raw provider payloads, full policy documents, full prompts, raw PII, and complete employee or reviewer free text.

#### Scenario: Sensitive metadata supplied
- **WHEN** a trace caller supplies nested metadata containing sensitive keys or disallowed text fields
- **THEN** exported metadata contains only allowed safe values or explicit redaction markers

#### Scenario: Identifier and metric metadata supplied
- **WHEN** a trace caller supplies approved identifiers, counts, categories, scores, versions, token usage, or durations
- **THEN** the safe metadata remains available for debugging and evaluation

### Requirement: Versioned golden datasets
The system SHALL maintain local machine-readable golden datasets for Policy Q&A and expense decisions with unique case identifiers, expected evidence or source identity, expected facts, and expected deterministic results where applicable.

#### Scenario: Golden dataset validation
- **WHEN** deterministic evaluation loads a golden dataset
- **THEN** every case satisfies the versioned schema, has a unique identifier, and contains the expected fields for its evaluation type

#### Scenario: Unsupported policy question
- **WHEN** a golden Policy Q&A case has no supported evidence
- **THEN** the expected outcome explicitly requires safe insufficient-information behavior

### Requirement: Deterministic quality metrics
The system SHALL calculate retrieval Precision@5, Recall@10, citation correctness, valid-citation coverage, and exact deterministic decision accuracy without an LLM judge. It MAY additionally calculate MRR and NDCG.

#### Scenario: Retrieval metric calculation
- **WHEN** ranked retrieval results are evaluated against expected evidence
- **THEN** Precision@5 and Recall@10 are calculated deterministically from identifiers and expected relevance

#### Scenario: Decision metric calculation
- **WHEN** expense golden cases are evaluated
- **THEN** exact decision accuracy compares deterministic decisions and expected values, with a required target of 1.00 for the controlled golden set

#### Scenario: Citation metric calculation
- **WHEN** generated citations are evaluated
- **THEN** correctness verifies retrieval membership, expected policy and section where specified, and current eligibility without an LLM judge

### Requirement: Retrieval strategy benchmark
The system SHALL benchmark vector-only, hybrid lexical-plus-vector with RRF, and hybrid-plus-reranking strategies using identical queries, filters, expected evidence, and non-production evaluator configuration.

#### Scenario: Comparable benchmark run
- **WHEN** the benchmark executes
- **THEN** it reports strategy, Precision@5, Recall@10, MRR when enabled, and average latency using the same golden cases for every strategy

#### Scenario: Production retrieval isolation
- **WHEN** benchmark-specific strategy selection is used
- **THEN** the running application's production retrieval configuration and persisted business state remain unchanged

### Requirement: Offline RAG quality evaluation
The system SHALL provide offline Ragas and DeepEval evaluation paths for generated-answer grounding, relevance, and context usage using APIs supported by the installed versions. These evaluations SHALL NOT execute synchronously in normal API requests.

#### Scenario: Evaluator credentials available
- **WHEN** an operator explicitly runs an external quality evaluation with required credentials
- **THEN** the runner evaluates the selected golden cases and writes a report with metric versions, scores, case outcomes, and errors

#### Scenario: Evaluator credentials unavailable
- **WHEN** the default CI or a local operator lacks optional evaluator credentials
- **THEN** deterministic gates still run and external evaluation reports a documented skip rather than failing the production application or default CI

### Requirement: Evaluation reports and regression thresholds
The system SHALL generate machine-readable reports and a human-readable summary containing dataset identity, configuration, metric definitions, per-case results, aggregates, latency, threshold outcomes, and execution errors. Deterministic retrieval thresholds SHALL be configurable; external-judge thresholds SHALL begin as recorded baselines until explicitly approved.

#### Scenario: Deterministic regression
- **WHEN** Precision@5, Recall@10, citation correctness, or deterministic decision accuracy falls below its configured gate
- **THEN** the deterministic evaluation command exits unsuccessfully and identifies the failing cases and metric

#### Scenario: External baseline run
- **WHEN** Ragas or DeepEval runs before an approved regression threshold exists
- **THEN** the report records baseline scores without inventing or enforcing an undocumented permanent threshold

### Requirement: Credential-free CI evaluation
The system SHALL run dataset validation, deterministic retrieval and citation checks, exact decision tests, mocked tracing tests, and report generation in CI without live LangSmith or model credentials. Live Ragas and DeepEval execution SHALL be separately opt-in or scheduled.

#### Scenario: Pull request without external credentials
- **WHEN** the evaluation workflow runs for a pull request with no external secrets
- **THEN** deterministic gates execute, reports are retained as workflow artifacts, and live evaluator steps are skipped

#### Scenario: Runtime/evaluation separation
- **WHEN** the production API starts or handles a request
- **THEN** it does not execute Ragas, DeepEval, retrieval benchmarks, or golden-dataset evaluation in the request path
