## Why

The starter repository cannot yet run or verify the platform as a whole. The first change establishes dependable local and CI infrastructure before expense, policy, or agent behavior is added.

## What Changes

- Run one modular FastAPI backend and one React/TypeScript frontend.
- Configure PostgreSQL 16, Redis, environment-driven settings, structured logs, health and dependency readiness.
- Add SQLAlchemy session management, Alembic bootstrap migration enabling pgvector, and four-service Docker Compose.
- Add focused backend tests, frontend build verification, and GitHub Actions CI.

## Capabilities

### New Capabilities

- `platform-foundation`: runnable applications, infrastructure, configuration, migration, operational endpoints, and CI.

## Impact

Only foundation files and tests are changed. Existing graph, RAG, gateway, domain, and review modules remain placeholders. No expense or policy endpoints are activated.
