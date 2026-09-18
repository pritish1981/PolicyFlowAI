## Purpose

Allows employees to submit structured expenses and receive persisted, evidence-grounded assessments while deterministic controls retain authority over monetary and documentation decisions.

## ADDED Requirements

### Requirement: Structured expense intake
The system SHALL accept `POST /api/v1/expenses` for HOTEL, MEAL, and TAXI expenses with positive two-decimal monetary amounts, INR currency, location, DOMESTIC or INTERNATIONAL travel type, business purpose, and receipt availability, and SHALL reject invalid values and unsupported fields with HTTP 422.

#### Scenario: Complete expense
- **WHEN** a caller submits a valid complete expense
- **THEN** the system creates a durable expense identifier and returns an assessment result with a stable thread identifier

#### Scenario: Invalid expense
- **WHEN** the amount is nonpositive or has excess precision, an enum is unsupported, or an unsupported field is supplied
- **THEN** the API returns HTTP 422 without creating a business record or invoking a model

### Requirement: Targeted clarification
The system SHALL detect missing assessment fields deterministically, persist a pending expense and resumable context, and return `INSUFFICIENT_INFORMATION` with the specific missing field names and `PROVIDE_CLARIFICATION` action. A later clarification SHALL resume the same expense and thread rather than creating another expense.

#### Scenario: Missing purpose
- **WHEN** an otherwise valid expense omits its business purpose
- **THEN** the response identifies `purpose` and does not evaluate policy or call a model

#### Scenario: Complete clarification
- **WHEN** the caller supplies missing information for a pending expense
- **THEN** assessment continues under its original expense and thread identifiers

### Requirement: Authoritative expense and assessment records
The system SHALL commit an authoritative expense record before long-running retrieval or model work and SHALL persist the final assessment separately, including decision, validated policy-rule lineage, citations, confidence, explanation, and model metadata. Monetary amounts SHALL retain decimal precision.

#### Scenario: Successful assessment
- **WHEN** a complete expense is assessed
- **THEN** the business records remain queryable independently of workflow execution state

#### Scenario: Workflow failure
- **WHEN** retrieval, storage, or model execution fails after expense creation
- **THEN** the expense remains in a controlled pending or failed state and no successful assessment is fabricated

### Requirement: Idempotent expense creation
The system SHALL accept an `Idempotency-Key` for expense creation, return the same resource and result for a repeated key and identical payload, and return HTTP 409 for a repeated key with different payload.

#### Scenario: Repeated request
- **WHEN** an identical submission repeats its key
- **THEN** no second expense or assessment is created

#### Scenario: Conflicting request
- **WHEN** the same key is reused with a different payload
- **THEN** the API returns HTTP 409 without changing the first expense

### Requirement: Eligible multi-policy evidence
The system SHALL use ACTIVE policies effective on the assessment date and not expired, retrieve category-specific and applicable documentation/exception evidence through the existing lexical and vector search, fusion, and reranking path, and validate cited chunks against authoritative storage.

#### Scenario: Hotel amount and receipt
- **WHEN** a hotel expense requires both an amount limit and a receipt rule
- **THEN** the assessment considers verified evidence for both conditions rather than filtering out the documentation policy

#### Scenario: No eligible evidence
- **WHEN** no valid applicable citations remain
- **THEN** the assessment returns `INSUFFICIENT_INFORMATION` without a fabricated policy limit or compliance decision

### Requirement: Structured policy-rule extraction
The system SHALL obtain schema-validated policy rules through the central Model Gateway using an expense-rule task and exact retrieved chunk IDs. The model output SHALL not supply the final compliance decision, and a rule with an unsupported source ID or invalid monetary value SHALL not authorize a decision.

#### Scenario: Applicable rules
- **WHEN** eligible evidence supports amount, receipt, and exception conditions
- **THEN** the structured result retains typed conditions and source IDs for deterministic validation and evaluation

#### Scenario: Invalid or unavailable model result
- **WHEN** extraction fails validation or the provider is unavailable after bounded handling
- **THEN** the API returns a controlled failure or safe insufficient-evidence result, never an unvalidated compliance decision

### Requirement: Deterministic expense decision
The system SHALL evaluate money, mandatory receipts, explicit prohibitions, and exception conditions in application code using validated evidence-derived rules and decimal arithmetic. It SHALL return only `COMPLIANT`, `NON_COMPLIANT`, `NEEDS_REVIEW`, or `INSUFFICIENT_INFORMATION`; it SHALL not autonomously approve an exception.

#### Scenario: Within standard limit
- **WHEN** an eligible expense is within its evidenced limit, required documentation is present, and all critical conditions are supported
- **THEN** the decision is `COMPLIANT` with the applicable limit and verified citations

#### Scenario: Above standard limit
- **WHEN** an eligible expense exceeds its evidenced limit and exception review is supported
- **THEN** the decision is `NEEDS_REVIEW` with a review next action but no reviewer workflow started

#### Scenario: Missing mandatory receipt or prohibition
- **WHEN** verified policy evidence establishes a mandatory receipt that is absent or an explicit prohibition that applies
- **THEN** the decision is `NON_COMPLIANT` with the relevant policy citation

#### Scenario: Incomplete or conflicting rules
- **WHEN** critical rule evidence is missing, citations fail, or applicable rules materially conflict
- **THEN** the decision is `INSUFFICIENT_INFORMATION` and no policy threshold is invented

### Requirement: Evidence-based confidence and traceability
The system SHALL derive confidence from deterministic evidence and rule-coverage signals, make insufficient evidence override any model self-confidence, and record sanitized request, thread, expense, retrieval, rule, citation, and decision metadata without secrets or full policy documents.

#### Scenario: Supported assessment
- **WHEN** all critical conditions have validated sources
- **THEN** the response includes bounded confidence and citations that resolve to stored policy sections

#### Scenario: Unsafe evidence
- **WHEN** critical evidence cannot be validated
- **THEN** confidence cannot promote the result to a material compliance decision

### Requirement: Expense assessment interface
The frontend SHALL provide a structured expense form with validation, loading/error/clarification states and an assessment view showing decision, policy limit, confidence, explanation, next action, and verified citations.

#### Scenario: Assessment display
- **WHEN** an assessment completes
- **THEN** the UI displays the decision and supporting policy identity and excerpt without presenting a pending exception as approved

#### Scenario: Clarification display
- **WHEN** required information is missing
- **THEN** the UI identifies the missing fields and allows the employee to supply them for the same expense
