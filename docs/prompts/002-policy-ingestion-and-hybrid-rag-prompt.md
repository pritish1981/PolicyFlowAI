Act as a Senior AI Systems Engineer. We are continuing implementation of PolicyFlow AI under the OpenSpec framework. Phase 001-platform-foundation is complete and verified.

Now implement Phase 002: `002-policy-ingestion-and-hybrid-rag` strictly adhering to FRD v1.0 and LLD v1.0 specifications.

--- OBJECTIVE ---
Build the complete Policy Ingestion and Hybrid RAG pipeline using PostgreSQL, pgvector, full-text search (FTS), Reciprocal Rank Fusion (RRF), Cohere/BGE reranking, and Citation Validation.

--- SCOPE OF CHANGES (002-POLICY-INGESTION-AND-HYBRID-RAG) ---

1. SYNTHETIC POLICY CORPUS (6-8 markdown files under `policies/synthetic/`):
   - POL-001: Travel & Expense Policy
   - POL-002: Hotel & Accommodation Policy (e.g., Domestic limit INR 7,000/night, International INR 15,000/night)
   - POL-003: Meal & Daily Allowance Policy (e.g., Domestic INR 1,500/day)
   - POL-004: Ground Transportation Policy (e.g., Airport Taxi limit INR 2,000/trip)
   - POL-005: Receipt & Documentation Policy (e.g., Mandatory receipt > INR 500)
   - POL-006: Expense Exception Policy

2. DATABASE & MIGRATIONS (`backend/app/db/` & `alembic/`):
   - Ensure pgvector and GIN extension migrations are ready.
   - Database tables: `rag.policy_document` and `rag.policy_chunk`.
   - Indexing:
     * GIN index on `policy_chunk.search_vector` (FTS).
     * HNSW vector index on `policy_chunk.embedding` (`vector_cosine_ops`).
     * GIN metadata index and B-tree active status/domain indexes.

3. INGESTION ENGINE (`backend/app/rag/ingestion/` & `chunking.py`):
   - Section-aware hierarchical chunker (400–700 token target, 50–100 token overlap, strictly preserving policy section boundaries).
   - Ingestion script/CLI (`scripts/ingest_policies.py`) with content hashing & Redis lock to prevent duplicate ingestion.
   - Metadata generator (assign policy_code, version, region, domain, section_id, active status, effective date).

4. HYBRID RETRIEVAL & FUSION ENGINE (`backend/app/rag/retrieval/` & `rrf.py`):
   - Metadata Filter Builder: Deterministic filtering by status (ACTIVE), domain, travel_type/region, and effective date.
   - Dual Retrieval: Fetch Top-20 FTS candidates (tsvector match) + Top-20 pgvector semantic candidates in parallel.
   - Reciprocal Rank Fusion (RRF): Fuse candidate lists using formula RRF(doc) = SUM(1 / (k + rank_i)) with default k=60. Deduplicate by `chunk_id`.

5. RERANKING & CITATION VALIDATION (`backend/app/rag/reranking/` & `citations.py`):
   - Model Adapter Interface: Implement Cohere Reranker adapter (primary) with BGE fallback adapter interface. Rerank Top-20 fused items to Top-3–5 final evidence chunks.
   - Citation Validator: Validate that all citations match active retrieved chunks, verify version/section bounds, and reject unverified/hallucinated policy references.

6. REST API & ADMIN ENDPOINTS (`backend/app/api/v1/admin.py` & `policy.py`):
   - Add `POST /api/v1/admin/policies/ingest` (Ingest/Re-index policies).
   - Add `POST /api/v1/policy/query` stub/testing route for policy search testing.

7. AUTOMATED TESTS (`backend/tests/`):
   - Unit tests for chunking boundary preservation, RRF score calculation, and Citation Validator.
   - Integration tests for hybrid PostgreSQL search (FTS + pgvector) and Alembic migrations.

--- EXECUTION RULES ---
- Strictly use Python 3.12, FastAPI, Pydantic v2, and SQLAlchemy/Alembic.
- Do NOT modify existing Phase 001 platform foundation backend/frontend configurations unless necessary for DB connection.
- Keep components modular and fully typed. Include clean docstrings.
- Output a summary of all created/modified files, run tests (`pytest backend/tests`), and confirm successful policy ingestion.

#### Changed Files in Phase 002

These are the files added or edited for Phase 002, grouped by purpose:
## OpenSpec:
[proposal.md](D:/git-repo/PolicyFlow-AI/openspec/changes/002-policy-ingestion-and-hybrid-rag/proposal.md),
[design.md](D:/git-repo/PolicyFlow-AI/openspec/changes/002-policy-ingestion-and-hybrid-rag/design.md),
[spec.md](D:/git-repo/PolicyFlow-AI/openspec/changes/002-policy-ingestion-and-hybrid-rag/specs/policy-ingestion-and-hybrid-rag/spec.md),
[tasks.md](D:/git-repo/PolicyFlow-AI/openspec/changes/002-policy-ingestion-and-hybrid-rag/tasks.md).
## Synthetic policies:
[POL-001](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-001-travel-expense-policy.md),
[POL-002](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-002-hotel-accommodation-policy.md),
[POL-003](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-003-meal-daily-allowance-policy.md),
[POL-004](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-004-ground-transportation-policy.md),
[POL-005](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-005-receipt-documentation-policy.md),
[POL-006](D:/git-repo/PolicyFlow-AI/policies/synthetic/POL-006-expense-exception-policy.md).
##Database:
[migration](D:/git-repo/PolicyFlow-AI/backend/alembic/versions/20260913_0002_policy_rag.py),
            [policy_document.py](D:/git-repo/PolicyFlow-AI/backend/app/models/policy_document.py),
			[policy_chunk.py](D:/git-repo/PolicyFlow-AI/backend/app/models/policy_chunk.py).
##Ingestion and embeddings:
                            [metadata.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/ingestion/metadata.py),
                            [chunker.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/ingestion/chunker.py),
							[loader.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/ingestion/loader.py),
							[embedding_provider.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/embeddings/embedding_provider.py),
							[ingest_policies.py](D:/git-repo/PolicyFlow-AI/scripts/ingest_policies.py).
## Retrieval and evidence:
                          [lexical_retriever.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/lexical_retriever.py),
                          [vector_retriever.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/vector_retriever.py),
						  [hybrid_retriever.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/hybrid_retriever.py),
						  [rrf.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/retrieval/rrf.py),
						  [validator.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/citations/validator.py).
##Reranking and API:
                     [base.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/base.py),
                     [cohere_reranker.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/cohere_reranker.py),
					 [bge_reranker.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/bge_reranker.py),
					 [reranking/__init__.py](D:/git-repo/PolicyFlow-AI/backend/app/rag/reranking/__init__.py),
					 [admin.py](D:/git-repo/PolicyFlow-AI/backend/app/api/v1/admin.py),
					 [policy.py](D:/git-repo/PolicyFlow-AI/backend/app/api/v1/policy.py),
					 [api/v1/__init__.py](D:/git-repo/PolicyFlow-AI/backend/app/api/v1/__init__.py).
##Configuration and documentation:
                                   [main.py](D:/git-repo/PolicyFlow-AI/backend/app/main.py),
                                   [config.py](D:/git-repo/PolicyFlow-AI/backend/app/core/config.py),
								   [requirements.txt](D:/git-repo/PolicyFlow-AI/backend/requirements.txt),
								   [Dockerfile](D:/git-repo/PolicyFlow-AI/backend/Dockerfile),
								   [docker-compose.yml](D:/git-repo/PolicyFlow-AI/docker-compose.yml),
								   [.dockerignore](D:/git-repo/PolicyFlow-AI/.dockerignore),
								   [.env.example](D:/git-repo/PolicyFlow-AI/.env.example),
								   [README.md](D:/git-repo/PolicyFlow-AI/README.md).
## Tests:
         [test_policy_rag.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_rag.py),
         [test_policy_rag_integration.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_rag_integration.py),
		 [test_policy_api_adapters.py](D:/git-repo/PolicyFlow-AI/backend/tests/test_policy_api_adapters.py).
