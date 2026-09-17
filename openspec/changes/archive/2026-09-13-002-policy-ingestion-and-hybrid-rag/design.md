## Context

FRD v1.0 FR-04 through FR-07 and FR-11 through FR-12 require deterministic eligibility, PostgreSQL FTS and pgvector search, RRF, reranking, and verified citations. LLD v1.0 section 9 requires transactional indexing.

## Decisions

- Store canonical documents/chunks in rag.policy_document and rag.policy_chunk. Use a generated tsvector and GIN index, vector(512) and HNSW cosine index, JSONB GIN, and status/domain B-tree indexes. GIN is an index method, not an extension.
- Use one configured local 512-dimensional long-context embedding model for ingestion and query. Persist model identity.
- Parse Markdown frontmatter and heading sections. Overlap only within a section; short sections remain short.
- Lock by code/version in Redis, hash source bytes, skip unchanged content, and commit replacement transactionally. Mark ACTIVE after chunks are stored.
- Apply ACTIVE, domain, region, travel type, and effective-date filters in SQL. Search FTS and vector independently, top 20 each, then fuse by chunk ID with RRF k=60.
- Cohere is primary reranker; lazy local BGE is fallback. Explicit RRF-only configuration is available for development. Return evidence, never generated policy advice.
- Validate citations against final hits and authoritative document version, section, status, and dates. Abstain if none survive.
- Protect ingestion API with an environment-supplied token; CLI uses same service.

## Risks

Local embedding/reranking models require downloads and disk. Load lazily and make adapters injectable for tests. Live ingestion requires the configured model.
