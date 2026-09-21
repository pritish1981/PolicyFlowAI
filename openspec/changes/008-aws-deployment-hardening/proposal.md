## Why

PolicyFlow AI is locally containerized but has no repeatable, secure cloud deployment: the AWS directories and deployment workflow are placeholders, migrations currently run in every Compose backend startup, and production networking, secrets, logging, rollback, and smoke validation are undefined. The final planned phase must make the portfolio POC deployable to AWS ECS/Fargate behind Cloudflare without changing the deterministic policy, expense, model-governance, HITL, or observability semantics completed in Phases 001-007.

## What Changes

- Add cost-conscious Terraform for a two-AZ VPC, public ALB, private Fargate application subnets, private RDS/ElastiCache database subnets, ECR, S3, Secrets Manager references, IAM, and CloudWatch Logs.
- Package the React frontend and FastAPI backend as hardened production containers with non-secret configuration, health checks, and traceable immutable image tags.
- Route browser traffic through Cloudflare and an HTTPS ALB, with frontend default routing and explicit backend API/health routes.
- Replace the placeholder AWS workflow with GitHub OIDC authentication, deterministic validation, ECR publishing, a one-off Alembic migration task, ECS rollout, stability waiting, smoke testing, and failure rollback guidance.
- Keep RDS and Redis private, restrict service traffic with security groups, encrypt supported storage, block public S3 access, and grant separate least-privilege ECS execution and application roles.
- Document Cloudflare DNS/TLS, initial Terraform/OIDC bootstrapping, pgvector verification, deployment, rollback, operations, cost controls, and cleanup.
- Preserve local Docker Compose behavior while removing migration execution from the production backend task startup path.
- Do not introduce Kubernetes/EKS, microservices, multi-region deployment, enterprise SSO, or automated creation of real AWS resources.

## Capabilities

### New Capabilities

- `aws-deployment-hardening`: Repeatable, private-by-default AWS ECS/Fargate deployment, edge ingress, secrets, observability, migration, CI/CD, validation, rollback, and cost/cleanup behavior for the PolicyFlow AI POC.

### Modified Capabilities

None. Existing application capability requirements remain unchanged; this phase packages and deploys them without altering business authority or workflow semantics.

## Impact

- **Containers:** backend and frontend Dockerfiles, nginx runtime configuration, Docker build contexts, and local Compose startup.
- **Runtime configuration:** production hosts/CORS, database pooling, Redis timeouts, health/readiness behavior, and non-secret environment variables.
- **Infrastructure:** new Terraform root under `infrastructure/terraform` and expanded AWS/Cloudflare documentation.
- **Delivery:** GitHub Actions CI and AWS deployment workflow using OIDC and SHA-tagged ECR images.
- **Operations:** explicit migration tasks, CloudWatch log groups, smoke tests, rollback, cost controls, and cleanup procedures.
- **External systems:** Cloudflare, ACM, ALB, ECS/Fargate, ECR, RDS PostgreSQL with pgvector, ElastiCache Redis, S3, Secrets Manager, CloudWatch, and GitHub Actions.
- **Compatibility:** public API and business decisions remain compatible with Phases 001-007. No real cloud resource is applied by this change implementation.
