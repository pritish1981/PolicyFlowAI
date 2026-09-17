## 1. Corpus and persistence
- [x] 1.1 Add six synthetic Markdown policies with validated metadata.
- [x] 1.2 Add models and Alembic migration with pgvector, FTS, and indexes.

## 2. Ingestion
- [x] 2.1 Implement section-aware chunking, metadata, embeddings, hash/idempotency, Redis lock, and transactional writes.
- [x] 2.2 Add CLI and admin API.

## 3. Retrieval and evidence
- [x] 3.1 Implement SQL filters, parallel FTS and vector retrieval, and RRF.
- [x] 3.2 Implement Cohere/BGE adapters and citation validation.
- [x] 3.3 Add evidence-only query API.

## 4. Verification
- [x] 4.1 Add unit and PostgreSQL integration tests including migrations.
- [x] 4.2 Run tests, migrate local DB, ingest corpus, verify live query.
