## 1. Configuration and backend shell

- [x] 1.1 Make database/Redis settings environment-required, configure CORS and JSON logging, and keep only foundation routes active.
- [x] 1.2 Implement `/health` and dependency-verifying `/ready` with safe failure responses and bounded timeouts.

## 2. Persistence and migration

- [x] 2.1 Complete SQLAlchemy engine/session dependency and Redis client handling.
- [x] 2.2 Configure Alembic from environment and add the pgvector extension bootstrap migration.

## 3. Local runtime and frontend

- [x] 3.1 Add backend/frontend services to Compose, environment examples, and startup instructions.
- [x] 3.2 Confirm the React/TypeScript shell builds and points to the backend health/readiness surface.
- [x] 3.3 Add a typed, reusable API client and modular frontend status display for backend, PostgreSQL, and Redis, including loading and error states.

## 4. Validation and CI

- [x] 4.1 Add meaningful health, readiness, configuration, and session tests.
- [x] 4.2 Add GitHub Actions backend pytest and frontend build jobs; validate locally and in Compose where available.
