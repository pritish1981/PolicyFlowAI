## Why

Phase 001 supplies the platform but no auditable policy corpus. FRD v1.0 requires versioned, eligible policy evidence.

## What Changes

- Add six synthetic expense policies and a section-aware ingestion pipeline.
- Persist documents/chunks in PostgreSQL with pgvector and full-text indexes.
- Add metadata filtering, dual retrieval, RRF, reranking, and citation validation.
- Add protected ingestion and evidence-only query APIs, CLI, and tests.

## Capabilities

### New Capabilities

- policy-ingestion-and-hybrid-rag: Transactional indexing and verified hybrid retrieval.

## Impact

Adds RAG tables, backend dependencies/configuration, routes, synthetic corpus, and CLI. PostgreSQL remains authoritative; Redis only coordinates ingestion.
