## 1. OpenSpec and Deployment Baseline

- [x] 1.1 Inspect repository Docker, CI, infrastructure, health, migration, configuration, and Phase 001-007 artifacts; verify the pre-implementation report records current state, gaps, architecture, and exact file scope.
- [x] 1.2 Reconcile FRD, HLD, LLD, project instructions, canonical specs, and current code; verify the design preserves business/checkpoint/Redis and deterministic/human authority boundaries.
- [x] 1.3 Validate the Phase 008 proposal, design, delta spec, and task structure strictly before implementation.

## 2. Production Container Hardening

- [x] 2.1 Add root and frontend Docker ignore rules; verify local environments, Git data, reports, Terraform state, and secret files cannot enter build contexts.
- [x] 2.2 Harden the Python 3.12 backend image with deterministic layers, non-root execution, production command, and health check; verify the image builds and contains no `.env` files.
- [x] 2.3 Harden the frontend multi-stage image with unprivileged nginx, SPA routing, `/healthz`, security headers, and cache rules; verify the image builds and serves its health path.
- [x] 2.4 Define same-origin frontend API configuration and preserve a local override; verify frontend tests and production build pass for both default and explicit base URLs.
- [x] 2.5 Separate local Compose migration execution from production service startup while preserving local PostgreSQL/Redis/backend/frontend behavior; verify Compose configuration renders successfully.

## 3. Cloud Runtime Configuration

- [x] 3.1 Add environment-aware trusted-host, documentation, database pool, connection timeout, Redis timeout/TLS, and production CORS settings; verify focused configuration tests cover safe defaults and overrides.
- [x] 3.2 Apply trusted-host and documentation settings at FastAPI startup without changing API routes or business behavior; verify health, readiness, and application import tests pass.
- [x] 3.3 Bound PostgreSQL and Redis connection behavior using settings; verify dependency failure remains observable through readiness and does not affect liveness.
- [x] 3.4 Add deployment smoke tooling for frontend, backend health, readiness, and optional pgvector checks; verify local mocked tests cover success and failure exits without cloud credentials.

## 4. Terraform Foundation and Network

- [x] 4.1 Add pinned Terraform/provider configuration, remote-state declaration, variables, validation, locals, tags, and outputs; verify `terraform fmt -check` and `terraform validate` pass.
- [x] 4.2 Define a two-AZ VPC with public ALB, private application, and isolated database subnets, routing, and one cost-conscious NAT gateway; verify the rendered dependency graph has no public database route.
- [x] 4.3 Define least-privilege ALB, ECS, RDS, and Redis security groups; verify only ALB-to-ECS, ECS-to-PostgreSQL, ECS-to-Redis, DNS, and required outbound HTTPS paths exist.

## 5. AWS Data, Registry, Secrets, IAM, and Logs

- [x] 5.1 Define separate immutable-tag ECR repositories for backend and frontend with scan-on-push and lifecycle policies; verify Terraform validation succeeds.
- [x] 5.2 Define encrypted private RDS PostgreSQL with subnet group, backups, POC sizing, and configurable deletion controls; verify public accessibility is disabled and only ECS ingress is accepted.
- [x] 5.3 Define private TLS-enabled ElastiCache Redis with subnet group and configurable POC sizing; verify it has no public ingress and only ECS access.
- [x] 5.4 Define an encrypted, versioned, public-access-blocked S3 policy/artifact bucket; verify backend task access is bucket-scoped.
- [x] 5.5 Define backend secret references without values and separate least-privilege execution, backend task, and frontend task roles; verify no administrator policy or committed secret value exists.
- [x] 5.6 Define encrypted backend, frontend, and migration CloudWatch log groups with finite configurable retention; verify each ECS container maps to its designated group.

## 6. ALB and ECS/Fargate

- [x] 6.1 Define the public ALB, HTTP-to-HTTPS redirect, ACM listener, frontend/backend target groups, health paths, and backend path rules; verify listener priority and routing are unambiguous.
- [x] 6.2 Define the ECS cluster and separate frontend/backend Fargate task definitions with private networking, immutable image tag input, health checks, logs, roles, and configurable POC CPU/memory; verify secrets appear only in the backend definition.
- [x] 6.3 Define independent frontend/backend ECS services with desired count one, ALB registration, deployment circuit breaker, and safe health grace settings; verify neither service assigns a public IP.
- [x] 6.4 Define a dedicated one-off backend migration task using the backend image and migration log group; verify it does not belong to an always-running service.

## 7. GitHub Actions CI/CD

- [x] 7.1 Extend pull-request CI with strict OpenSpec validation, Terraform format/validate, and backend/frontend Docker build checks; verify default CI needs no AWS or model-provider credentials.
- [x] 7.2 Replace the AWS placeholder with GitHub OIDC authentication, SHA-tagged ECR builds/pushes, and task definition rendering; verify no static AWS key or secret value exists in workflow source.
- [x] 7.3 Add one-off ECS migration execution, stopped-task/exit-code validation, service updates, and stability waits; verify a migration failure prevents service rollout.
- [x] 7.4 Add public smoke validation and prior-task-definition rollback handling; verify failed rollout instructions restore task revisions without downgrading the database.

## 8. Cloudflare and Operations Documentation

- [x] 8.1 Document Cloudflare proxied DNS, Full (strict) TLS, ACM validation, edge rate/WAF controls, cache exclusions, and optional origin hardening; verify no real domain is hardcoded.
- [x] 8.2 Replace AWS placeholder documents with network, ALB, ECS/migration, RDS/pgvector, Redis, Secrets Manager/IAM, and CloudWatch operational guidance; verify each document matches Terraform behavior.
- [x] 8.3 Add a complete deployment runbook covering prerequisites, remote-state/OIDC bootstrap, secret population, plan/apply approval boundary, deploy flow, smoke tests, rollback, cost drivers, and cleanup; verify commands are checkout-aware and non-destructive by default.
- [x] 8.4 Update README, local validation, Makefile, and Phase 008 prompt inventory/status; verify Phase 001-008 status and local/cloud validation boundaries are accurate and non-duplicative.

## 9. Verification and Completion

- [x] 9.1 Run focused deployment/configuration tests plus all Phase 001-007 backend regressions; verify every collected test passes without live AWS, Cloudflare, model, or LangSmith access.
- [x] 9.2 Run frontend tests and production build; verify no existing Policy Q&A, expense, or reviewer UI regression.
- [x] 9.3 Build both production Docker images and inspect runtime user, health checks, and contents; verify images contain no environment files or credentials.
- [x] 9.4 Run Compose config/startup regression and health/readiness checks where Docker is available; verify local development remains usable.
- [x] 9.5 Run Terraform format, validate, static security assertions, and a non-destructive plan only when account context permits; record plan limitations honestly and do not apply.
- [x] 9.6 Validate GitHub Actions YAML and audit files for secrets, public database/Redis exposure, mutable-only image deployment, generated state, whitespace, and unrelated changes.
- [x] 9.7 Run strict target, canonical-spec, and repository-wide OpenSpec validation; align all checkboxes only with completed evidence.
- [x] 9.8 Produce the Phase 008 implementation report with changed files, architecture, security, CI/CD, migration, Cloudflare, smoke, rollback, costs, cleanup, commands/results, unresolved deployment-time inputs, and POC limitations; stop without creating real cloud resources.
