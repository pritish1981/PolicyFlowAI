## Context

The starter has a FastAPI root and health route, Vite app, SQLAlchemy base/session stubs, and a Compose file with only PostgreSQL and Redis. Its default database URL and Alembic ini embed credentials; there is no readiness probe, migration version, Redis client, structured logging, backend/frontend Compose services, or meaningful tests. FRD v1.0, HLD v1.0, and LLD v1.0 support one backend with PostgreSQL authoritative and Redis transient.

## Goals / Non-Goals

Goals: make the foundation runnable locally and in Compose, with reproducible migration, dependency readiness, and CI evidence. Non-goals: LangGraph, RAG, model calls, reranking, expense evaluation, HITL, cloud deployment, and domain tables.

## Decisions

1. `DATABASE_URL` and `REDIS_URL` are required application environment variables. The committed `.env.example` has local-only sample values; no credential appears in Python or Alembic ini. Compose uses these variables and requires `POSTGRES_PASSWORD` for the database container. Local developers copy `.env.example` and load it through Pydantic settings or Compose.
2. `GET /health` is process liveness and performs no I/O. `GET /ready` runs `SELECT 1` and Redis `PING` with bounded connection timeouts. It returns 200 only when both succeed; otherwise 503 and a component-level status without credentials or exception text.
3. Use a synchronous SQLAlchemy 2 engine/session for the initial API. The FastAPI generator dependency owns and closes each request session. Redis is a small client module; no durable data is stored there.
4. Alembic reads `DATABASE_URL` from environment and migration `0001` executes `CREATE EXTENSION IF NOT EXISTS vector`. The pgvector PostgreSQL 16 image provides the extension binaries. No business tables are created in this phase.
5. Use JSON application logs on stdout with level, logger, message, and UTC timestamp. Exclude secrets and exception internals from readiness responses.
6. CORS origins are configured with a comma-separated environment variable; default local development origin is `http://localhost:5173`. Compose builds both apps, applies the migration before starting Uvicorn, and exposes the frontend on 5173. The frontend uses one typed API client and a status hook for `/health` and `/ready`; a 503 readiness response still supplies separate PostgreSQL and Redis states. Compose passes `VITE_API_BASE_URL` at image build time because Vite embeds it in the bundle.
7. Tests inject/check dependency behavior without requiring real services. A separate optional Compose smoke verifies live PostgreSQL/Redis and the extension. CI runs backend tests and frontend TypeScript/Vite build.

## Design Reconciliation / Decision Required

No blocking source conflict was found. The FRD/HLD/LLD describe later domain and AI features, deliberately excluded here. Operational defaults chosen above can be revised in later changes: Redis 7, local HTTP ports 8000/5173, and JSON logs. Production secret delivery and cloud deployment are outside this phase.

## Risks / Trade-offs

The frontend is a minimal shell. Live readiness depends on both services, while liveness remains available during outages. The initial migration does not define domain schema, keeping later persistence design open.
