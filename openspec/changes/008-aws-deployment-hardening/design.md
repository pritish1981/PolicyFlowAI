## Context

See `proposal.md` for motivation. The repository has working local Docker Compose, production-oriented application behavior through Phase 007, basic Dockerfiles, CI, `/health` and `/ready`, and placeholder AWS/Cloudflare directories. It has no functional IaC or AWS deployment pipeline. Compose starts Alembic inside backend startup, which must not be copied to a horizontally scalable ECS service. The FRD, HLD, and LLD require Cloudflare, ALB, separate frontend/backend Fargate services, RDS PostgreSQL with pgvector, ElastiCache, S3, Secrets Manager, ECR, CloudWatch, and GitHub Actions.

The POC must remain understandable and cost-conscious. Only synthetic data is allowed. PostgreSQL business records remain authoritative; LangGraph checkpoints are execution state; Redis is transient; models and observability never gain decision authority. Implementation prepares and validates deployment artifacts but does not apply them to a real AWS account.

## Goals / Non-Goals

**Goals:**

- Define a repeatable, reviewable AWS deployment with private stateful services and least-privilege connectivity.
- Produce hardened, independently deployable frontend and backend containers.
- Use immutable image identity, serialized migrations, observable rollout, smoke validation, and revision-based rollback.
- Support Cloudflare Full (strict) TLS to an ACM-protected ALB origin.
- Preserve local development and all Phase 001-007 behavior.
- Make CPU, memory, sizes, retention, domain, and availability trade-offs configurable.

**Non-Goals:**

- EKS/Kubernetes, service mesh, Kafka, microservice decomposition, multi-region active-active, or multi-account governance.
- Automatic application of Terraform, creation of paid resources, DNS mutation, or secret population during this implementation.
- Enterprise SSO, sophisticated autoscaling, automated disaster recovery, or mandatory Cloudflare authenticated origin pulls.
- Changes to policy retrieval, deterministic rules, model routing, HITL authority, or observability/evaluation semantics.

## Decisions

### 1. Use one flat Terraform root

`infrastructure/terraform` will contain a small flat configuration rather than many modules. The configuration will pin compatible Terraform/AWS provider versions, accept environment inputs, use consistent tags, validate variables, and expose deployment outputs. A configurable S3 backend supports persistent CI state after a documented one-time bootstrap.

Terraform was selected because no IaC exists and it provides readable plans and broad AWS coverage. CDK was rejected because it adds a second application/runtime toolchain; raw CloudFormation was rejected because the equivalent configuration is more verbose for this portfolio POC.

### 2. Use a two-AZ VPC with one POC NAT gateway

The ALB spans two public subnets. Frontend and backend tasks run in two private application subnets without public IPs. RDS and Redis use two isolated database subnets. A single NAT gateway in one public subnet provides outbound HTTPS for ECR image pulls and external model/tracing APIs.

One NAT gateway is a deliberate cost/availability compromise. Two NAT gateways are configurable as a future production hardening step. Public ECS tasks were rejected because they weaken the origin boundary. A large VPC-endpoint set does not remove the need for outbound model-provider access and can cost more than one POC NAT gateway.

### 3. Use one public ALB with path routing

The default action targets the frontend. `/api/*`, `/health`, `/ready`, `/docs*`, and `/openapi.json` target the backend. Port 80 redirects to 443; port 443 uses a caller-supplied ACM certificate. Frontend target health uses `/healthz`; backend target health uses `/health`. `/ready` is reserved for rollout smoke checks so temporary dependency trouble does not continuously recycle otherwise healthy tasks.

Separate public hostnames were rejected because same-origin routing avoids unnecessary CORS and frontend environment complexity. The ALB security group permits HTTP/HTTPS ingress; Cloudflare-origin-only enforcement is documented as an optional hardening step because Cloudflare IP ranges evolve and authenticated origin support requires external certificate lifecycle choices.

### 4. Build two minimal production containers

The frontend uses a Node build stage and unprivileged nginx runtime with SPA fallback, `/healthz`, conservative security headers, and immutable-asset caching. `VITE_API_BASE_URL` defaults to an empty same-origin base and never contains secrets.

The backend uses Python 3.12 slim, installs pinned project requirements, creates a non-root user, copies only required runtime code and policy fixtures, and starts Uvicorn directly. A root `.dockerignore` prevents Git data, local environments, caches, reports, and secrets from entering its root build context.

### 5. Separate migration from service startup

The ECS backend task definition provides both an application container definition and a migration task definition using the same immutable image. GitHub Actions runs one migration task with `python -m alembic upgrade head`, waits for STOPPED, and requires exit code zero before services update. The service command never runs Alembic. Compose may retain an explicit local migration command because it has one backend instance, but it will be clearly separated from production behavior.

Schema downgrades are never automatic. Rollback restores prior task definitions while leaving additive database migrations in place; incompatible future migrations must use expand/contract design.

### 6. Keep one encrypted POC RDS instance with logical separation

RDS PostgreSQL is private, encrypted, single-AZ by default, deletion protection configurable, and uses a database subnet group. Alembic enables `vector` and creates `app`, `rag`, `audit`, and `checkpoint` schemas. A single database/instance is retained for cost control. The migration task verifies the actual RDS extension rather than assuming Docker parity.

The database password is generated by Secrets Manager/RDS management where supported and the backend receives a complete connection URL from a separately populated Secrets Manager secret. This avoids committing secret material but requires an operator bootstrap step to set deploy-time values.

### 7. Treat Redis as a private transient dependency

ElastiCache uses a private subnet group and ECS-only security group. One small node is the default. TLS-in-transit is enabled and the application URL uses `rediss://`; application behavior continues to treat Redis as cache, lock, rate, and budget coordination only. Readiness reports Redis loss, while no business truth is recovered from it.

### 8. Use secret references and distinct IAM roles

The ECS execution role receives standard ECR/log permissions plus explicit `secretsmanager:GetSecretValue` access only to configured backend secrets. The backend task role receives only scoped S3 object/list access to the policy bucket. The frontend task role has no application AWS permissions. No administrator or wildcard resource policy is attached where a concrete ARN can be used.

Secrets are referenced, not assigned values, by Terraform. Rotation requires forcing a new ECS deployment because environment-injected secrets are read at task start.

### 9. Use SHA images and GitHub OIDC

CI validates tests, OpenSpec, Terraform formatting/validation, and container builds. The manually dispatched/main deployment job assumes a narrowly trusted AWS role through GitHub OIDC, logs in to ECR, publishes both images using `${GITHUB_SHA}`, renders new task revisions, runs migration, updates services, waits for stability, and performs public smoke checks. A convenience `latest` tag may be pushed, but task definitions use the SHA.

Long-lived AWS keys in GitHub secrets were rejected. Initial OIDC role and Terraform-state bootstrap remain explicit operator steps because a pipeline cannot safely create its own first trust path.

### 10. Split operational logs from AI traces

Dedicated encrypted CloudWatch log groups for backend, frontend, and migrations use configurable finite retention. JSON application logs go to stdout/stderr. LangSmith remains optional and handles minimized AI trace metadata only. ALB/ECS/RDS metrics can be viewed in CloudWatch; expensive third-party operational tooling is not added.

### 11. Harden runtime configuration without changing business behavior

Production settings add trusted hosts, documentation exposure control, database pool size/timeouts, Redis timeouts/TLS compatibility, and environment-aware CORS. Configuration remains fail-fast for required database/Redis URLs. Liveness checks only process health; readiness checks PostgreSQL and Redis with bounded timeouts and excludes model/trace providers.

## Risks / Trade-offs

- **Single NAT gateway creates an AZ dependency and recurring cost** -> document the trade-off, make subnet layout explicit, and allow production operators to extend to one NAT per AZ.
- **Single-AZ RDS and one Redis node reduce availability** -> keep defaults POC-sized and expose variables for stronger production settings.
- **Cloudflare proxy still leaves the ALB DNS name discoverable** -> require HTTPS at origin and document optional Cloudflare IP restrictions or authenticated origin pulls without freezing changing IP ranges into Terraform.
- **Terraform cannot populate provider secrets safely** -> create secret containers/references only and require out-of-band secret values before task launch.
- **Remote Terraform state and OIDC have bootstrap dependencies** -> provide exact one-time setup and validation instructions; never commit state or credentials.
- **Migration succeeds but new service fails** -> capture previous task definitions, restore them on failed stability/smoke checks, and never auto-downgrade schema.
- **RDS pgvector availability differs by engine version/region** -> make engine version configurable and require migration/extension verification against the target instance.
- **Frontend build-time configuration can become stale** -> use same-origin relative API URLs so domain changes do not require a secret or environment-specific API host.
- **AWS plan cannot be fully produced without account context** -> run offline `terraform validate`; report a plan as pending unless credentials and explicit non-destructive authorization exist.

## Migration Plan

1. Create and strictly validate the Phase 008 OpenSpec artifacts.
2. Harden both containers and production configuration; run unit, integration, frontend, and Docker validation.
3. Add Terraform resources, format and validate them, and review a non-destructive plan when account context is available.
4. Add OIDC-based CI/CD, one-off migration, service rollout, stability waiting, smoke testing, and rollback handling.
5. Bootstrap remote state and GitHub OIDC manually in the selected AWS account.
6. Populate Secrets Manager values out of band and request/validate the ACM certificate.
7. Apply Terraform only after separate explicit user authorization.
8. Push SHA images, run the migration task, deploy services, and validate CloudWatch logs and public health/readiness.
9. Configure Cloudflare proxied DNS and Full (strict) TLS, then execute the portfolio scenarios.

Rollback captures prior ECS task definition ARNs before updating. On service or smoke failure, restore both prior revisions and wait for stability. Database schema is not downgraded automatically. Infrastructure cleanup uses a reviewed Terraform destroy after retaining any required logs, artifacts, or snapshots.

## Open Questions

- The real domain name, ACM certificate ARN, AWS region/account, Terraform state bucket, GitHub deployment role ARN, and production secret ARNs remain deployment-time inputs. They do not change the architecture or task breakdown.
