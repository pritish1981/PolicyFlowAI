##Prompt-1
We are implementing the first OpenSpec change for the PolicyFlow AI project:

`001-platform-foundation`

PolicyFlow AI is an Enterprise Expense Compliance & Exception Agent.

For this change, implement ONLY the platform foundation. Do not implement LangGraph workflows, RAG, OpenAI/model integrations, reranking, expense compliance logic, or HITL yet.

Target stack:

* Python 3.12
* FastAPI
* Pydantic v2
* SQLAlchemy 2
* Alembic
* PostgreSQL 16 with pgvector extension
* Redis
* React + TypeScript + Vite
* Docker Compose
* Pytest
* GitHub Actions

The repository already contains starter frontend/backend folders and placeholder modules.

Please first inspect:

* README.md
* docker-compose.yml
* backend/
* frontend/
* openspec/
* docs/
* tests/

Then prepare the OpenSpec artifacts for `001-platform-foundation`.

The change must establish:

1. Runnable FastAPI backend.
2. Runnable React + TypeScript frontend.
3. PostgreSQL connectivity.
4. pgvector extension enabled through migration.
5. Redis connectivity.
6. SQLAlchemy database session handling.
7. Alembic migrations.
8. Application configuration through environment variables.
9. Structured application logging.
10. `/health` endpoint.
11. `/ready` readiness endpoint that verifies PostgreSQL and Redis.
12. CORS configuration for local React development.
13. Docker Compose for PostgreSQL, Redis, backend, and frontend.
14. Basic unit/integration tests.
15. GitHub Actions CI for backend tests and frontend build.

Architecture constraints:

* Keep this as one modular FastAPI backend, not microservices.
* PostgreSQL is authoritative persistent storage.
* Redis is non-authoritative infrastructure.
* Secrets must come from environment variables.
* Do not hard-code credentials in application code.
* Keep placeholders for later LangGraph/RAG/Model Gateway phases, but do not implement them.
* Use clean separation between API, core/configuration, database, schemas, repositories, and services.

Before writing implementation code, produce/review the OpenSpec proposal/design/tasks for this change and identify any missing decisions.

Then implement the tasks incrementally and validate each major step.

##Prompt-002
Continue OpenSpec change `001-platform-foundation`.

The backend foundation is complete and verified:

* FastAPI is running.
* `/health` works.
* `/ready` verifies PostgreSQL and Redis.
* PostgreSQL, pgvector, Redis, and Alembic are configured.

Implement only the React platform foundation.

Requirements:

1. Use the existing React + TypeScript + Vite frontend.
2. Create a simple PolicyFlow AI landing page.
3. Create a reusable API client using the configured `VITE_API_BASE_URL`.
4. Call the backend `/health` endpoint.
5. Call the backend `/ready` endpoint.
6. Display:

   * Backend status
   * PostgreSQL status
   * Redis status
7. Show loading and error states cleanly.
8. Keep the UI simple and professional.
9. Do not implement expense forms, policy Q&A, LangGraph, RAG, Model Gateway, or HITL.
10. Keep components modular and TypeScript types explicit.

After implementation:

* list files changed,
* run `npm run build`,
* report any errors,
* do not proceed to Docker integration automatically.
