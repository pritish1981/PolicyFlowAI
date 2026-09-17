## Purpose

Establishes the runnable application shells, dependency checks, persistence bootstrap, and delivery checks needed before PolicyFlow AI adds expense and agent behavior.

## ADDED Requirements

### Requirement: Runnable application shells
The system SHALL run a Python 3.12 FastAPI backend and React/TypeScript/Vite frontend as separate services, with the backend remaining a single modular application.

#### Scenario: Start application shells
- **WHEN** the documented local or Compose startup is followed
- **THEN** the backend serves `/health` and the frontend serves its foundation page

### Requirement: Frontend platform status
The frontend SHALL use the configured `VITE_API_BASE_URL` to call `/health` and `/ready`, and SHALL display separate backend, PostgreSQL, and Redis states with loading and error feedback.

#### Scenario: Dependencies ready
- **WHEN** the backend health and readiness endpoints respond successfully
- **THEN** the page shows the backend, PostgreSQL, and Redis as available

#### Scenario: Dependency unavailable
- **WHEN** `/ready` responds 503 with component statuses
- **THEN** the page shows the reported PostgreSQL and Redis states separately

#### Scenario: Backend unreachable
- **WHEN** a status request fails due to a network error
- **THEN** the page shows an error state without claiming the dependency is healthy

### Requirement: Environment configuration and logging
The backend SHALL obtain database and Redis URLs from environment variables and emit structured application logs. It SHALL allow configured local React origins through CORS.

#### Scenario: Missing connection settings
- **WHEN** a required connection URL is absent
- **THEN** application startup fails with a configuration error rather than using embedded credentials

#### Scenario: Local browser request
- **WHEN** a request originates from an allowed React development origin
- **THEN** the backend supplies the corresponding CORS headers

### Requirement: Dependency probes
The backend SHALL expose `/health` for liveness and `/ready` for PostgreSQL and Redis readiness.

#### Scenario: Both dependencies available
- **WHEN** PostgreSQL answers `SELECT 1` and Redis answers `PING`
- **THEN** `/ready` responds 200 with both components ready

#### Scenario: Dependency unavailable
- **WHEN** either dependency fails its check
- **THEN** `/ready` responds 503 with component statuses and no connection credentials

### Requirement: Persistence foundation
The backend SHALL provide SQLAlchemy 2 session handling and Alembic migration support, with PostgreSQL as authoritative persistence. The initial migration SHALL enable the pgvector extension. Redis SHALL remain non-authoritative.

#### Scenario: Apply initial migration
- **WHEN** Alembic upgrade runs against PostgreSQL 16 with pgvector installed
- **THEN** the `vector` extension exists and Alembic can advance through the migration chain

### Requirement: Foundation delivery checks
Docker Compose SHALL define PostgreSQL, Redis, backend, and frontend. CI SHALL run backend pytest and a frontend production build.

#### Scenario: Continuous integration
- **WHEN** a push or pull request runs CI
- **THEN** backend tests and frontend TypeScript/Vite build are executed
