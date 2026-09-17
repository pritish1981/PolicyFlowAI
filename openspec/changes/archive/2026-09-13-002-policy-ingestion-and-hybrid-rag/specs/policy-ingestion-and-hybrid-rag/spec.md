## Purpose

Provides versioned synthetic policy evidence through controlled ingestion, eligible hybrid retrieval, reranking, and citation checks without making expense decisions.

## ADDED Requirements

### Requirement: Versioned policy ingestion
The system SHALL validate metadata, hash content, coordinate duplicate attempts with Redis, preserve section boundaries, and commit document/chunk records transactionally before marking a document ACTIVE.

#### Scenario: Unchanged source
- **WHEN** the same code, version, and content hash are ingested
- **THEN** no duplicate chunks are created

#### Scenario: Oversized section
- **WHEN** a section exceeds the target size
- **THEN** chunks remain within that section and overlap only there

### Requirement: Authoritative hybrid retrieval
The system SHALL use PostgreSQL indexed FTS and pgvector and SHALL filter ACTIVE status, domain, region, travel type, and effective date before ranking.

#### Scenario: Eligible query
- **WHEN** an eligible query is submitted
- **THEN** FTS and vector searches each return at most 20 candidates and RRF deduplicates by chunk ID using k=60 by default

#### Scenario: Ineligible policy
- **WHEN** a policy is inactive or outside requested metadata or date bounds
- **THEN** its chunks do not appear

### Requirement: Reranked verified citations
The system SHALL rerank fused candidates and SHALL validate final citations against chunk ID, policy/version/section, ACTIVE status, and effective interval.

#### Scenario: Hallucinated citation
- **WHEN** a citation references a missing chunk or mismatched metadata
- **THEN** it is rejected

#### Scenario: No verified evidence
- **WHEN** no citations survive validation
- **THEN** the response abstains

### Requirement: Administrative ingestion
The system SHALL expose token-protected ingestion and an evidence-only query API.

#### Scenario: Unauthorized ingestion
- **WHEN** the admin token is missing or invalid
- **THEN** the request is denied
