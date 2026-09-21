# PolicyFlow AI AWS Deployment Runbook

This runbook prepares and operates the Phase 008 portfolio POC. It does not
authorize Terraform apply, DNS changes, secret creation, or resource deletion.
Use only synthetic/public data.

## Architecture

    Cloudflare (DNS, TLS, edge controls)
      -> public AWS ALB (HTTP redirect, HTTPS listener)
         -> frontend target group -> private ECS/Fargate frontend
         -> backend target group  -> private ECS/Fargate backend
                                      -> private RDS PostgreSQL + pgvector
                                      -> private ElastiCache Redis
                                      -> encrypted private S3 bucket
                                      -> OpenAI/Cohere/LangSmith via NAT HTTPS

GitHub Actions assumes an AWS role through OIDC, pushes Git-SHA images to ECR,
runs one migration task, updates both services, waits for stability, and runs
public smoke checks. Operational logs go to CloudWatch; LangSmith remains the
optional AI-tracing layer.

## Prerequisites and deployment-time inputs

- Terraform 1.8-1.x, AWS CLI v2, Docker, Python 3.12, Node.js 20, and Git.
- An AWS account and selected region with two available AZs.
- A Cloudflare-managed hostname such as policyflow.example.com.
- A validated ACM certificate in the ALB region.
- A pre-created encrypted, versioned S3 Terraform-state bucket.
- A GitHub OIDC deploy role restricted to this repository and the aws-poc environment.
- GitHub environment variables listed under CI/CD below.

Never place credentials in terraform.tfvars, task JSON, workflow source, or Git.
terraform.tfvars.example contains placeholders only.

## 1. Bootstrap Terraform state and GitHub OIDC

The Terraform state bucket and first GitHub trust role are bootstrap resources;
they cannot safely be created by the deployment that depends on them. Create
them once using an approved administrator workflow. Scope the OIDC trust to:

    repo:pritish1981/PolicyFlowAI:environment:aws-poc

Grant only the resource-management permissions needed by this Terraform root
and ECS/ECR deployment. Do not grant AdministratorAccess.

Initialize from the repository root:

    Copy-Item infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/poc.auto.tfvars
    # Replace placeholders; do not commit poc.auto.tfvars.
    terraform -chdir=infrastructure/terraform init `
      -backend-config="bucket=<state-bucket>" `
      -backend-config="key=policyflow/poc/terraform.tfstate" `
      -backend-config="region=<aws-region>" `
      -backend-config="encrypt=true" `
      -backend-config="use_lockfile=true"

Review without changing AWS:

    terraform -chdir=infrastructure/terraform fmt -check
    terraform -chdir=infrastructure/terraform validate
    terraform -chdir=infrastructure/terraform plan -out=policyflow.tfplan
    terraform -chdir=infrastructure/terraform show policyflow.tfplan

terraform apply requires separate explicit approval. A plan can still read AWS
state and refresh data, but it does not create resources.

## 2. Review security and cost before apply

Confirm the plan shows:

- ALB in two public subnets.
- ECS tasks in private application subnets with assign_public_ip false.
- RDS and Redis in isolated database subnets with no default internet route.
- RDS publicly_accessible false.
- RDS/Redis ingress only from the ECS security group.
- ECS application ports exposed only to the ALB security group.
- S3 public access blocked, encryption and versioning enabled.
- Separate execution, backend-task, and frontend-task roles.
- Immutable ECR repositories and finite CloudWatch retention.
- One NAT gateway, one small RDS instance, one Redis node, and desired ECS
  service count one by default.

Main recurring cost drivers are the ALB, NAT gateway/data, Fargate tasks, RDS,
ElastiCache, CloudWatch ingestion/retention, and public IPv4/EIP. Cloudflare,
model providers, Cohere, and LangSmith can add separate charges.

## 3. Apply only after approval

After an authorized plan review:

    terraform -chdir=infrastructure/terraform apply policyflow.tfplan
    terraform -chdir=infrastructure/terraform output

This command intentionally is not run by Phase 008 implementation.

## 4. Populate Secrets Manager

Terraform creates secret containers but never creates secret values. Populate:

- /<project>-<environment>/DATABASE_URL
- /<project>-<environment>/REDIS_URL
- /<project>-<environment>/OPENAI_API_KEY
- /<project>-<environment>/COHERE_API_KEY
- /<project>-<environment>/LANGSMITH_API_KEY
- /<project>-<environment>/POLICY_ADMIN_TOKEN

Use a postgresql+psycopg RDS URL and a rediss ElastiCache URL. Secret objects
referenced by the task definition must have current versions. After rotation,
force a new backend deployment so new tasks read the rotated values.

## 5. Validate RDS and pgvector

The migration task runs:

    python -m alembic upgrade head

Migration 0001 executes CREATE EXTENSION IF NOT EXISTS vector; later migrations
create the app, rag, audit, and checkpoint logical areas. From an approved
private-network administration path run:

    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
    SELECT version_num FROM alembic_version;

Expected Alembic head is 20260920_0004. Do not assume the local pgvector image
proves that the selected RDS engine and region support the required extension.

## 6. Configure GitHub environment variables

In the protected aws-poc environment configure:

- AWS_REGION
- AWS_DEPLOY_ROLE_ARN
- ECR_BACKEND_REPOSITORY and ECR_FRONTEND_REPOSITORY
- ECS_CLUSTER
- ECS_BACKEND_SERVICE and ECS_FRONTEND_SERVICE
- ECS_BACKEND_TASK_FAMILY, ECS_FRONTEND_TASK_FAMILY, ECS_MIGRATION_TASK_FAMILY
- ECS_SUBNET_IDS as comma-separated subnet IDs
- ECS_SECURITY_GROUP_ID
- APPLICATION_URL, including https://

The workflow uses no long-lived AWS access-key secrets. Run Deploy AWS manually
and type DEPLOY. It publishes SHA tags, registers task revisions, runs and
verifies one migration task, and only then updates services.

## 7. Configure Cloudflare and TLS

Create a proxied CNAME:

    policyflow.example.com -> <alb_dns_name Terraform output>

Use Cloudflare SSL/TLS mode Full (strict). The ALB certificate must cover the
public hostname. Keep /api/*, /health, and /ready out of HTML caching. Enable
reasonable managed WAF and rate controls. Never proxy or publish RDS/Redis.

The ALB remains an HTTPS origin even if its DNS name is discovered. For stronger
origin restriction, separately evaluate maintained Cloudflare IP ingress rules
or authenticated origin pulls/mTLS. These are optional because IP ranges and
certificate lifecycle require ownership outside this repository.

## 8. Smoke validation

After service stability:

    python scripts/deployment_smoke.py --base-url https://policyflow.example.com --timeout 15

Expected: the frontend, /health, and /ready return HTTP 200; readiness reports
PostgreSQL and Redis ready. From a trusted database network path, add
--database-url <private-url> to verify pgvector. Provider and LangSmith
reachability are deliberately excluded from liveness.

Then validate the portfolio scenarios: cited Policy Q&A; INR 9500 hotel
NEEDS_REVIEW; exception interrupt/reviewer/resume; LangSmith AI spans plus
CloudWatch operational logs.

## 9. Rollback

The workflow captures current backend/frontend task definition ARNs before
rollout. A failed rollout or smoke check restores those revisions and waits for
stability. Manual equivalent:

    aws ecs update-service --cluster <cluster> --service <backend-service> --task-definition <previous-backend-arn>
    aws ecs update-service --cluster <cluster> --service <frontend-service> --task-definition <previous-frontend-arn>
    aws ecs wait services-stable --cluster <cluster> --services <backend-service> <frontend-service>

Never run automatic alembic downgrade during rollback. Use backward-compatible
expand/contract schema changes.

## 10. Cleanup

Cleanup is destructive and requires explicit approval. Export required logs,
artifacts, policy sources, or snapshots first. Review safeguards, then:

    terraform -chdir=infrastructure/terraform plan -destroy
    terraform -chdir=infrastructure/terraform destroy

Finally remove Cloudflare DNS, ACM validation records, OIDC role, and Terraform
state only after confirming no other environment uses them.

## Limitations

- No real account, domain, certificate, secrets, plan, apply, or deployed smoke
  result is claimed by repository-only validation.
- Defaults are portfolio POC choices: one NAT gateway, single-AZ RDS, one Redis
  node, and no sophisticated autoscaling.
- Authenticated origin pulls, enterprise SSO, multi-region DR, deployment
  alarms, and blue/green orchestration remain out of scope.
