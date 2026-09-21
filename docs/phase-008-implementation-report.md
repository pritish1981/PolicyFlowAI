# Phase 008 AWS Deployment Hardening — Implementation Report

## Outcome

The repository now contains a complete, repeatable AWS portfolio-POC deployment
definition for Cloudflare -> ALB -> separate private frontend/backend
ECS/Fargate services -> private RDS PostgreSQL/pgvector, private ElastiCache
Redis, and encrypted S3. GitHub Actions builds immutable images, runs one
Alembic migration task, rolls services out, waits for stability, smoke-tests,
and restores prior task revisions on failure.

No Terraform apply, AWS resource mutation, Cloudflare change, or secret value
creation occurred. Account-, domain-, and credential-dependent validation
remains pending explicit deployment authorization.

## 1. OpenSpec

Created proposal, design, 11 behavioral requirements with scenarios, and 41
traceable tasks under openspec/changes/008-aws-deployment-hardening. The change
preserves all Phase 001-007 authority boundaries and excludes EKS, microservice
decomposition, multi-region, enterprise SSO, and complex blue/green tooling.

## 2. Docker changes

- Backend: Python 3.12 slim, runtime-only requirements, virtual environment,
  non-root policyflow user, explicit Uvicorn production command, liveness check,
  no embedded environment files.
- Frontend: Node 20 build stage, unprivileged nginx runtime, SPA fallback,
  /healthz, security headers, immutable asset caching, and no-cache HTML.
- Same-origin API is the production default; local Compose supplies
  http://localhost:8000 at build time.
- Root/frontend ignore files exclude secrets, state, reports, caches, and local
  dependencies from build contexts.

## 3. Infrastructure files

Terraform under infrastructure/terraform defines version/provider locking,
remote S3 state declaration, validated variables, network, security groups,
ECR, RDS, ElastiCache, S3, Secrets Manager references, IAM, CloudWatch, ALB,
ECS task definitions/services, migration task, and outputs.

## 4. VPC and network

- Two public ALB subnets in two AZs.
- Two private application subnets for ECS without public IPs.
- Two isolated database subnets without an internet default route.
- One shared NAT gateway is the explicit POC cost/availability compromise.
- VPC DNS is enabled for AWS and external dependency resolution.

## 5. ECS

The cluster runs independent frontend and backend services at desired count one
by default. Both use Fargate, private networking, deployment circuit breakers,
CloudWatch logs, container health checks, configurable CPU/memory, and
SHA-tagged images. The migration task is a task definition only and is never an
always-running service.

## 6. ALB

The public ALB spans both public subnets. HTTP redirects to HTTPS. ACM-backed
HTTPS routes default traffic to frontend port 8080 and API/health/readiness/docs
paths to backend port 8000. ALB liveness uses frontend /healthz and backend
/health; deployment smoke uses /ready.

## 7. RDS and pgvector

RDS is private, encrypted, single-AZ by default, backup-enabled, configurable
for deletion protection/final snapshot, and accessible only from ECS on 5432.
Alembic creates vector plus app, rag, audit, and checkpoint logical areas. Live
RDS extension support must be checked after an authorized deployment.

## 8. Redis

ElastiCache is private, encryption-at-rest and in-transit enabled, single-node
by default, and accessible only from ECS on 6379. Redis remains transient; it is
not business or checkpoint truth.

## 9. S3

The account-suffixed policy/artifact bucket blocks all public access, enables
AES-256 server-side encryption and versioning, and expires noncurrent versions
after 30 days. It does not store authoritative business state.

## 10. Secrets Manager

Terraform creates secret containers without values for DATABASE_URL, REDIS_URL,
OPENAI_API_KEY, COHERE_API_KEY, LANGSMITH_API_KEY, and POLICY_ADMIN_TOKEN.
Values are populated out of band. Rotation requires a new backend task.

## 11. IAM

The execution role has standard ECR/log permissions plus explicit access to the
defined secret ARNs. The backend task role has only list/get/put access to its
artifact bucket. The frontend task role has no application AWS policy. No
AdministratorAccess policy is defined.

## 12. CloudWatch

Separate backend, frontend, and migration log groups use finite configurable
retention. AWS encrypts CloudWatch Logs at rest. CloudWatch owns operational
logs; LangSmith continues to own minimized AI traces.

## 13. GitHub Actions

CI now runs backend/frontend gates, strict OpenSpec validation, Terraform
format/validate, and both container builds. The manual aws-poc deployment uses
GitHub OIDC, an explicit DEPLOY confirmation, protected environment variables,
separate ECR repositories, and immutable Git SHA tags. No static AWS access keys
or secret values appear in workflow source.

## 14. Migration strategy

The pipeline registers the SHA migration task, runs exactly one Fargate task,
waits for it to stop, and requires exit code zero before either service update.
Production backend startup never runs Alembic. Local Compose retains a single
pre-start migration for developer convenience.

## 15. Cloudflare and TLS

Operations create a proxied CNAME to the ALB output, use Full (strict) mode and
a matching regional ACM certificate, exempt API/health paths from HTML caching,
and enable reasonable edge WAF/rate controls. Cloudflare IP restrictions or
authenticated origin pulls are documented optional extensions.

## 16. CORS, hosts, pools, and timeouts

Production uses same-origin requests and the configured HTTPS domain for CORS.
A selective Trusted Host middleware protects browser/API traffic while allowing
ALB private-IP /health probes. PostgreSQL pool/connect values and Redis
connect/socket timeouts are bounded configuration. API docs can be disabled.

## 17. Smoke tests

scripts/deployment_smoke.py validates frontend availability, backend liveness,
dependency readiness, and optionally pgvector. Unit tests cover success/failure.
The workflow runs it only after ECS services become stable.

## 18. Rollback

The workflow captures current backend/frontend task definition ARNs before
rollout. A failure restores both revisions and waits for stability. Database
schema is never automatically downgraded; future changes must use
backward-compatible expand/contract migrations.

## 19. Cost considerations

Defaults use one NAT gateway, one small single-AZ RDS instance, one small Redis
node, one task per service, finite logs, and no EKS. ALB, NAT/data, public IPv4,
Fargate, RDS, Redis, logs, Cloudflare, and model/trace providers are the main
recurring costs.

## 20. Cleanup

The runbook requires exporting needed evidence/snapshots, reviewing retention
safeguards, creating a destroy plan, and obtaining destructive approval before
Terraform destroy. Cloudflare, ACM validation, OIDC, and remote state are
removed only after confirming they are not shared.

## 21. Commands executed

- Pinned OpenSpec new/status/instructions/strict validate.
- Pytest focused and complete suites through uv/Python 3.12.
- npm test, build, and production dependency audit.
- Docker Compose config, build/start, ps, HTTP health/readiness, and PostgreSQL
  pgvector/Alembic queries.
- Direct backend/frontend Docker builds plus user, health-check, and file
  inspection.
- Terraform 1.9.8 container fmt, init -backend=false, validate, and fmt -check.
- PyYAML workflow parsing and actionlint.
- Git whitespace, ignore, secret-signature, and changed-file audits.

## 22-26. Validation evidence

- Backend focused deployment/IaC gate: 10 passed.
- Complete backend/regression gate: 135 passed, with two existing non-failing
  dependency deprecation warnings.
- Frontend: 2 tests passed; Vite production build passed.
- Docker: backend and frontend images built; UID 100 policyflow and UID 101
  nginx; no runtime .env files; frontend /healthz HTTP 200.
- Compose: all four services healthy; /health and /ready HTTP 200.
- Local PostgreSQL: pgvector 0.8.6; Alembic head 20260920_0004.
- Terraform: initialized with AWS provider 5.100.0; format and validate passed.
- GitHub Actions: YAML parsed and actionlint passed.
- npm production dependencies: 0 vulnerabilities.
- OpenSpec: target change valid; canonical specs 7 passed/0 failed;
  repository-wide 8 passed/0 failed.

No Terraform plan was generated because no AWS account, remote backend, domain,
certificate, or credentials were placed in scope. This is the designed
non-destructive boundary, not evidence of an applied deployment.

## 27. Unresolved deployment-time inputs

- AWS account/region and approved cost budget.
- Remote-state bucket and GitHub OIDC role.
- Public domain, Cloudflare zone, and ACM certificate ARN.
- Secret values and final provider/model choices.
- Confirmed regional RDS PostgreSQL/pgvector compatibility.

## 28. POC limitations

Single NAT, single-AZ RDS, one Redis node, desired count one, no autoscaling
sophistication, no WAF-as-code at Cloudflare, no mTLS/AOP, no enterprise SSO,
no multi-region DR, and no real-cloud evidence until apply.

## 29. End-to-end deployment flow

    review tests/spec/IaC
      -> build SHA frontend/backend images
      -> GitHub OIDC -> ECR
      -> register migration task -> Alembic head
      -> register/update backend and frontend services
      -> ECS stability -> public smoke
      -> Cloudflare -> HTTPS ALB -> private Fargate
      -> private RDS/Redis/S3; CloudWatch logs; optional LangSmith traces

The deployment layer observes and hosts existing capabilities; it does not
change deterministic policy decisions, citations, reviewer authority, or
business truth.
