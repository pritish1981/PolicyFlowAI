## Purpose

Provides a durable, auditable human review workflow for justified expense exceptions while keeping reviewer actions authoritative and AI assistance evidence-grounded and non-binding.

## ADDED Requirements

### Requirement: Controlled exception submission
The system SHALL accept an exception justification only for an existing expense with a persisted `NEEDS_REVIEW` assessment, SHALL reject blank, undersized, oversized, ineligible, or already-finalized submissions, and SHALL prevent duplicate uncontrolled exception records.

#### Scenario: Eligible exception
- **WHEN** an employee submits a valid justification for a `NEEDS_REVIEW` expense
- **THEN** the system persists one exception with the original expense, assessment, and thread identifiers and returns `PENDING_REVIEW` with `WAIT_FOR_REVIEW`

#### Scenario: Ineligible assessment
- **WHEN** an employee submits an exception for a COMPLIANT, NON_COMPLIANT, or missing assessment
- **THEN** the system rejects the request without creating an exception or starting human review

#### Scenario: Duplicate exception
- **WHEN** an active or finalized exception already exists for the assessment
- **THEN** the system returns the existing controlled state or HTTP 409 without creating another exception

### Requirement: Deterministic review context
The system SHALL calculate monetary variance as the expense amount minus the evidenced policy limit using decimal arithmetic, retain a null variance when no numeric limit exists, and present only authoritative expense, assessment, policy, justification, and server-side citation data to the reviewer.

#### Scenario: Numeric policy limit
- **WHEN** an INR 9500 expense has an evidenced INR 7000 limit
- **THEN** the persisted and displayed variance is INR 2500.00

#### Scenario: No numeric limit
- **WHEN** the assessment has no applicable numeric policy limit
- **THEN** the exception remains reviewable with a null variance

### Requirement: Non-authoritative evidence-grounded summary
The system SHALL request any exception summary through the central Model Gateway using only supplied expense facts, deterministic variance, employee justification, and verified citations. The output SHALL be schema validated, SHALL cite only supplied chunk identifiers, and SHALL not contain or control an approval decision.

#### Scenario: Valid summary
- **WHEN** the summary provider returns schema-valid grounded content
- **THEN** the reviewer sees a neutral summary, key facts, attention points, and valid citation references labeled as AI-generated and non-authoritative

#### Scenario: Summary failure
- **WHEN** the summary provider is unavailable or its output is invalid
- **THEN** the authoritative exception remains pending and reviewable from deterministic facts and evidence with summary unavailability recorded

### Requirement: Durable human review interrupt and resume
The system SHALL interrupt the existing exception workflow at human review, persist compact execution state in PostgreSQL checkpoint storage, and resume the same workflow thread after a reviewer action, including after process recreation. Checkpoint state SHALL NOT be authoritative business truth.

#### Scenario: Pending human review
- **WHEN** exception collection completes
- **THEN** the workflow interrupts with a bounded reviewer payload and the API returns the persisted pending-review business state

#### Scenario: Same-thread resume
- **WHEN** a reviewer acts on a pending exception
- **THEN** the workflow resumes from the stored checkpoint using the original thread identifier rather than starting a new workflow

#### Scenario: Checkpoint unavailable after business commit
- **WHEN** a review action is durably committed but workflow resume temporarily fails
- **THEN** the business decision remains authoritative and retryable reconciliation does not duplicate the reviewer action

### Requirement: Reviewer queue and evidence detail
The system SHALL provide demo-role-protected pending review and detail views containing the minimum expense, assessment, policy, variance, justification, summary status, and verified citation metadata needed for review, without exposing checkpoint internals or secrets.

#### Scenario: Reviewer views queue
- **WHEN** an authorized demo reviewer requests pending reviews
- **THEN** the system returns only exceptions currently awaiting reviewer action

#### Scenario: Reviewer views evidence
- **WHEN** an authorized demo reviewer opens a pending exception
- **THEN** the system returns policy code, version, section, server-side excerpt, expense facts, variance, and justification from authoritative records

#### Scenario: Unauthorized role
- **WHEN** a non-reviewer calls a reviewer endpoint
- **THEN** the system returns HTTP 403 without exposing review details

### Requirement: Authoritative reviewer decisions
The system SHALL allow an authorized human reviewer to select only APPROVE, REJECT, or REQUEST_MORE_INFORMATION with validated comments. It SHALL persist the reviewer identity and action in business tables; no model output SHALL make or override that action.

#### Scenario: Approve
- **WHEN** a reviewer approves a pending exception
- **THEN** the system records the review, marks the exception APPROVED, finalizes the expense outcome, records audit data, and resumes the same workflow thread

#### Scenario: Reject
- **WHEN** a reviewer rejects a pending exception
- **THEN** the system records the review, marks the exception REJECTED, finalizes the expense outcome, records audit data, and resumes the same workflow thread

#### Scenario: Request more information
- **WHEN** a reviewer requests more information from a pending exception
- **THEN** the system records that action, marks the exception MORE_INFORMATION_REQUIRED, and returns `PROVIDE_MORE_INFORMATION` without treating the case as approved or rejected

### Requirement: More-information continuation
The system SHALL accept additional employee information only for `MORE_INFORMATION_REQUIRED` exceptions, preserve the exception and workflow identifiers, append rather than erase prior review history, and return the case to `PENDING_REVIEW` for a later reviewer action.

#### Scenario: Employee supplies follow-up
- **WHEN** an employee submits valid additional information for a `MORE_INFORMATION_REQUIRED` exception
- **THEN** the system retains the original exception and thread, records the new information, and makes the case pending review again

#### Scenario: Follow-up in invalid state
- **WHEN** additional information is submitted for a pending or finalized exception
- **THEN** the system returns HTTP 409 without changing the case

### Requirement: Atomic and idempotent finalization
The system SHALL lock and validate the pending exception, insert the reviewer action, update exception and expense outcome, and append the audit event in one business transaction. A second conflicting or final decision SHALL return HTTP 409 and SHALL NOT alter the first decision.

#### Scenario: Concurrent final decisions
- **WHEN** two reviewers concurrently submit final actions for the same pending exception
- **THEN** exactly one final action commits and the other request returns HTTP 409

#### Scenario: Repeated final decision
- **WHEN** a reviewer submits a decision after the exception is finalized
- **THEN** the system returns HTTP 409 without inserting another final review or audit outcome

### Requirement: Append-only audit and correlation
The system SHALL append sanitized audit events for exception creation, human-review interruption, reviewer action, more-information continuation, workflow resume, and finalization with request, thread, expense, exception, review, actor, previous-state, and new-state identifiers where applicable.

#### Scenario: Finalized exception trace
- **WHEN** an exception reaches APPROVED or REJECTED
- **THEN** its business records and audit events reconstruct the human-owned transition independently of checkpoint tables

### Requirement: Employee and reviewer interfaces
The frontend SHALL let an employee submit justification for a `NEEDS_REVIEW` assessment, provide requested follow-up information, and view pending or final status. It SHALL let an authorized demo reviewer list pending exceptions, inspect evidence, and submit one supported action with comments.

#### Scenario: Employee submits justification
- **WHEN** an employee views a `NEEDS_REVIEW` result
- **THEN** the interface presents justification input and displays the resulting pending-review status without implying approval

#### Scenario: Reviewer completes an action
- **WHEN** a reviewer submits a valid action from the detail view
- **THEN** the interface disables duplicate submission while pending and displays the authoritative returned state and reviewer comments
