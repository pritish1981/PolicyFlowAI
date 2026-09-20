## MODIFIED Requirements

### Requirement: Deterministic expense decision
The system SHALL evaluate money, mandatory receipts, explicit prohibitions, and exception conditions in application code using validated evidence-derived rules and decimal arithmetic. It SHALL return only `COMPLIANT`, `NON_COMPLIANT`, `NEEDS_REVIEW`, or `INSUFFICIENT_INFORMATION`; it SHALL not autonomously approve an exception. A persisted `NEEDS_REVIEW` assessment SHALL remain the immutable assessment basis for a later human-owned exception outcome.

#### Scenario: Within standard limit
- **WHEN** an eligible expense is within its evidenced limit, required documentation is present, and all critical conditions are supported
- **THEN** the decision is `COMPLIANT` with the applicable limit and verified citations

#### Scenario: Above standard limit
- **WHEN** an eligible expense exceeds its evidenced limit and exception review is supported
- **THEN** the decision is `NEEDS_REVIEW` with an exception-submission next action but no approval or rejection

#### Scenario: Missing mandatory receipt or prohibition
- **WHEN** verified policy evidence establishes a mandatory receipt that is absent or an explicit prohibition that applies
- **THEN** the decision is `NON_COMPLIANT` with the relevant policy citation

#### Scenario: Incomplete or conflicting rules
- **WHEN** critical rule evidence is missing, citations fail, or applicable rules materially conflict
- **THEN** the decision is `INSUFFICIENT_INFORMATION` and no policy threshold is invented

#### Scenario: Human exception outcome
- **WHEN** an authorized reviewer later approves or rejects an exception for a `NEEDS_REVIEW` assessment
- **THEN** the system exposes the human-owned exception outcome separately without rewriting the original deterministic assessment decision

### Requirement: Expense assessment interface
The frontend SHALL provide a structured expense form with validation, loading/error/clarification states and an assessment view showing decision, policy limit, confidence, explanation, next action, and verified citations. For `NEEDS_REVIEW`, it SHALL allow controlled exception submission and display later human-owned exception status without presenting pending review or AI-generated content as approval.

#### Scenario: Assessment display
- **WHEN** an assessment completes
- **THEN** the UI displays the decision and supporting policy identity and excerpt without presenting a pending exception as approved

#### Scenario: Clarification display
- **WHEN** required information is missing
- **THEN** the UI identifies the missing fields and allows the employee to supply them for the same expense

#### Scenario: Exception continuation
- **WHEN** a `NEEDS_REVIEW` assessment is eligible for exception handling
- **THEN** the UI permits justification submission and displays pending, more-information-required, approved, or rejected exception status as a separate human-review outcome
