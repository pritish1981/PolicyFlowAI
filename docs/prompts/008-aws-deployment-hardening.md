You are acting as a Principal Cloud/AI Engineer and Senior DevOps developer implementing the final OpenSpec change for the PolicyFlow AI project.

PROJECT
-------
Project name:
PolicyFlow AI — Enterprise Expense Compliance & Exception Agent

Repository root:
D:\git-repo\PolicyFlow-AI

Current OpenSpec change:
008-aws-deployment-hardening

Source-of-truth documents:
- docs/requirements/PolicyFlow_AI_FRD_v1.0.docx
- docs/architecture/PolicyFlow_AI_HLD_v1.0.docx
- docs/architecture/PolicyFlow_AI_LLD_v1.0.docx
- openspec/project.md
- existing specifications under openspec/specs/
- completed OpenSpec changes:
  - 001-platform-foundation
  - 002-policy-ingestion-and-hybrid-rag
  - 003-policy-qa
  - 004-expense-compliance-assessment
  - 005-exception-hitl
  - 006-model-gateway-guardrails
  - 007-observability-evaluation
- current repository implementation

TARGET DEPLOYMENT
-----------------
Cloudflare
    ->
AWS Application Load Balancer
    ->
ECS/Fargate
    -> React frontend container
    -> FastAPI backend container
    ->
RDS PostgreSQL + pgvector
    ->
ElastiCache Redis
    ->
S3
    ->
Secrets Manager

Container images:
GitHub Actions -> ECR -> ECS/Fargate

Observability:
LangSmith for AI tracing
CloudWatch for AWS/container logs and operational visibility

============================================================
0. BEFORE WRITING CODE
============================================================

Before modifying anything:

1. Inspect the full repository.
2. Inspect:
   - infrastructure/
   - infra/
   - docker-compose.yml
   - frontend/Dockerfile
   - backend/Dockerfile
   - .github/workflows/
   - backend/app/core/config.py
   - backend/app/api/routes/health.py
   - backend/app/api/v1/health.py
   - backend/alembic/
   - README.md
3. Inspect completed OpenSpec changes 001-007.
4. Inspect existing:
   - Dockerfiles
   - environment configuration
   - health/readiness endpoints
   - Alembic startup behavior
   - GitHub Actions
   - any existing AWS IaC
   - Cloudflare documentation/config
5. Determine whether infrastructure uses:
   - Terraform
   - CloudFormation
   - CDK
   - shell scripts
   - manual AWS CLI
6. Prefer the infrastructure style already present.
7. Do not introduce Kubernetes/EKS.
8. Do not create microservices.
9. Do not change application business semantics.
10. Do not change RAG/LLM/HITL decisions.
11. Do not expose databases publicly.
12. Do not hardcode secrets.
13. Do not automatically provision expensive production-grade resources beyond POC requirements.
14. Keep the deployment understandable for a single-engineer portfolio project.

Before coding, provide:
- current deployment state;
- existing Docker/CI state;
- current infrastructure files;
- deployment gaps;
- proposed architecture;
- exact files you intend to create/modify.

============================================================
1. PHASE 008 OBJECTIVE
============================================================

Deploy and harden PolicyFlow AI as a containerized AWS portfolio POC.

The final runtime architecture must be:

Internet
   |
   v
Cloudflare
   |
   v
AWS ALB
   |
   v
ECS/Fargate
   |
   +--> React frontend container
   |
   +--> FastAPI backend container
             |
             +--> RDS PostgreSQL + pgvector
             |
             +--> ElastiCache Redis
             |
             +--> S3
             |
             +--> OpenAI / Cohere via outbound HTTPS
             |
             +--> LangSmith via outbound HTTPS

Images:
GitHub Actions
   ->
Amazon ECR
   ->
ECS task definitions/services

Secrets:
AWS Secrets Manager
   ->
ECS task injection / secure runtime retrieval

Logs:
ECS/Fargate
   ->
CloudWatch Logs

============================================================
2. OPENSPEC WORKFLOW
============================================================

Inspect:

openspec/changes/008-aws-deployment-hardening/

If incomplete, create/update:

openspec/changes/008-aws-deployment-hardening/
    proposal.md
    design.md
    tasks.md
    specs/
        aws-deployment-hardening/
            spec.md

Follow the same OpenSpec structure used in earlier phases.

Proposal must explain:
- why AWS deployment is needed;
- why ECS/Fargate was chosen;
- why Kubernetes/EKS is intentionally out of scope;
- network topology;
- RDS/Redis/S3/Secrets Manager/ECR roles;
- Cloudflare integration;
- CI/CD;
- health checks;
- migration strategy;
- rollback strategy;
- secrets/security;
- logging;
- cost-conscious POC constraints;
- deployment validation.

Design must cover:
- VPC/subnets;
- security groups;
- ALB listeners/target groups;
- ECS cluster/services;
- task definitions;
- frontend/backend containers;
- RDS PostgreSQL + pgvector;
- logical schemas/checkpoint DB considerations;
- Redis;
- S3;
- Secrets Manager;
- ECR;
- CloudWatch;
- GitHub Actions;
- Cloudflare;
- DNS/TLS;
- environment configuration;
- database migration execution;
- health checks;
- smoke tests;
- rollback;
- failure handling;
- least-privilege IAM;
- cost constraints.

Validate OpenSpec before implementation.

============================================================
3. STRICT PHASE 008 SCOPE
============================================================

IMPLEMENT:

A. production-ready Dockerfiles
B. multi-stage frontend build if appropriate
C. backend production container
D. ECR repositories
E. ECS cluster
F. ECS task definitions
G. ECS backend service
H. ECS frontend service
I. ALB
J. target groups
K. VPC/subnet/security-group design
L. RDS PostgreSQL
M. pgvector support
N. Redis/ElastiCache
O. S3 policy storage/artifact bucket
P. Secrets Manager
Q. IAM task roles
R. CloudWatch logs
S. GitHub Actions build/deploy
T. database migration deployment strategy
U. Cloudflare DNS/TLS integration
V. health/readiness configuration
W. deployment smoke tests
X. rollback procedure
Y. operational documentation
Z. OpenSpec completion

DO NOT IMPLEMENT:

- Kubernetes/EKS
- Kafka
- multi-region active-active
- service mesh
- complex blue/green platform unless already present
- production enterprise SSO
- WAF rules beyond reasonable Cloudflare/ALB POC configuration
- expensive enterprise observability platforms
- unnecessary managed services
- multi-account AWS organization
- full disaster recovery automation
- autoscaling sophistication beyond reasonable POC setup

============================================================
4. INFRASTRUCTURE-AS-CODE DECISION
============================================================

Inspect existing infrastructure first.

If Terraform already exists:
continue Terraform.

If AWS CDK already exists:
continue CDK.

If CloudFormation already exists:
continue CloudFormation.

If no IaC exists:
prefer a simple, understandable option consistent with project constraints.

Suggested preference for this POC:

Terraform OR AWS CDK

but DO NOT introduce a tool unnecessarily if existing scripts already satisfy the OpenSpec design.

The goal is:
repeatable infrastructure,
not tool showcase.

============================================================
5. NETWORK DESIGN
============================================================

Design a small but sensible VPC.

Preferred logical layout:

VPC
|
+-- Public subnet A
|     ALB
|
+-- Public subnet B
|     ALB
|
+-- Private application subnet A
|     ECS/Fargate
|
+-- Private application subnet B
|     ECS/Fargate
|
+-- Private database subnet A
|     RDS
|     ElastiCache
|
+-- Private database subnet B
      RDS
      ElastiCache

For a cost-conscious POC, simplify if required, but:

RDS must not be publicly reachable.

ElastiCache must not be publicly reachable.

ECS tasks should be reachable only through ALB where appropriate.

Do not expose backend containers directly to Internet.

============================================================
6. SECURITY GROUPS
============================================================

Create least-privilege rules.

ALB SG:
Inbound:
443 from Internet / Cloudflare-compatible design
80 only if redirecting HTTP -> HTTPS

Outbound:
frontend/backend target ports

ECS SG:
Inbound:
only from ALB SG on application ports

Outbound:
RDS
Redis
HTTPS external APIs
required AWS services

RDS SG:
Inbound:
PostgreSQL 5432 only from ECS SG

Redis SG:
Inbound:
Redis port only from ECS SG

Do not use 0.0.0.0/0 for database access.

============================================================
7. APPLICATION LOAD BALANCER
============================================================

Use ALB as the AWS application ingress.

Possible routing:

/
-> frontend target group

/api/*
-> backend target group

/health
-> backend or appropriate health route

Or use separate hostnames if current architecture prefers:

app.<domain>
api.<domain>

Use whichever matches existing project design.

Configure:
- target health checks;
- deregistration;
- HTTP -> HTTPS redirect where appropriate;
- TLS via ACM if used at ALB.

Do not invent unnecessary routing complexity.

============================================================
8. FRONTEND CONTAINER
============================================================

Inspect current React Dockerfile.

Prefer multi-stage build:

Node build stage
    ->
npm ci
npm run build
    ->
static runtime stage

Runtime may use:
- nginx
or equivalent existing lightweight server.

Requirements:
- production build;
- configurable API base URL strategy;
- no secrets in frontend;
- cache headers where reasonable;
- health endpoint/static availability.

Remember:
VITE_* variables are normally build-time variables.

Do not put OpenAI keys or backend secrets in frontend environment variables.

============================================================
9. BACKEND CONTAINER
============================================================

FastAPI production container should:

- use Python 3.12;
- install only required dependencies;
- run as non-root if practical;
- expose backend port;
- use production ASGI server setup;
- support environment configuration;
- have health endpoint;
- have readiness endpoint;
- avoid including secrets in image layers;
- use slim base image if compatible.

Do not embed .env files into Docker image.

Do not bake provider keys into image.

============================================================
10. ECS/FARGATE
============================================================

Create ECS cluster.

Create separate services for:

policyflow-frontend
policyflow-backend

Each service should use:
- Fargate launch type;
- task definition;
- private networking;
- CloudWatch logs;
- health checks;
- ECR images.

For a POC start small.

Example:
desired_count = 1

Do not provision excessive task sizes.

Make CPU/memory configurable.

============================================================
11. ECS TASK EXECUTION ROLE VS TASK ROLE
============================================================

Use separate concepts correctly.

Task execution role:
- pull images from ECR;
- send logs to CloudWatch;
- access Secrets Manager required for task startup.

Application task role:
- access S3 if backend uses it;
- access additional AWS APIs only when required.

Use least privilege.

Do not attach AdministratorAccess.

AWS ECS recommends using dedicated IAM roles for tasks and task execution, with Secrets Manager access granted explicitly when required. :contentReference[oaicite:4]{index=4}

============================================================
12. AMAZON ECR
============================================================

Create ECR repositories:

policyflow-backend
policyflow-frontend

GitHub Actions should:

build image
tag image
push image

Tag strategy:

git SHA
and optionally:
latest for demo convenience

Do not deploy only mutable `latest` if a SHA tag is available.

Task definitions should reference immutable or traceable image tags.

============================================================
13. RDS POSTGRESQL
============================================================

Provision PostgreSQL in RDS.

Requirements:

- private subnet;
- no public accessibility;
- security group restricted to ECS;
- encrypted storage;
- automated backups appropriate for POC;
- pgvector extension compatibility;
- connection string supplied securely.

Use one instance for POC if current design does.

Keep logical separation:

app schema
rag schema
audit schema

LangGraph checkpoint schema/database logically separate.

This aligns with the project assumption that one RDS instance may host logically separated data stores for cost control. :contentReference[oaicite:5]{index=5}

============================================================
14. PGVECTOR VALIDATION
============================================================

Confirm RDS PostgreSQL engine/version supports the pgvector extension version needed.

Deployment validation must include:

CREATE EXTENSION IF NOT EXISTS vector;

or Alembic equivalent.

Do not assume local Docker pgvector behavior maps identically to RDS.

Run migration verification after connection.

============================================================
15. ALEMBIC MIGRATION STRATEGY
============================================================

Do not let multiple ECS tasks race migrations at startup.

Preferred strategies:

Option A:
GitHub Actions runs a one-off ECS task:
alembic upgrade head

Then deploy service.

Option B:
dedicated migration task/job.

Avoid:
every backend container automatically running migrations concurrently.

Document chosen strategy.

Deployment sequence:

build
    ->
push
    ->
migration task
    ->
deploy backend
    ->
health check

============================================================
16. ELASTICACHE REDIS
============================================================

Provision Redis-compatible ElastiCache according to existing code compatibility.

Use it only for:
- transient cache;
- rate limiting;
- locks;
- token budget counters;
- coordination.

Redis is NOT business truth.

Requirements:
- private network;
- SG ECS-only;
- secure connection if supported/configured;
- connection info from environment/secrets/config.

Application must preserve Phase 001-007 semantics if Redis becomes temporarily unavailable according to existing design.

============================================================
17. S3
============================================================

Use S3 for:

synthetic policy source documents
optional evaluation artifacts
optional deployment artifacts

Do NOT move authoritative business state to S3.

Bucket requirements:
- block public access;
- encryption at rest;
- least-privilege backend task access;
- environment-specific naming or suffixing.

Do not store credentials in S3.

============================================================
18. SECRETS MANAGER
============================================================

Store sensitive values such as:

DATABASE_URL or DB credentials
OPENAI_API_KEY
COHERE_API_KEY if used
LANGSMITH_API_KEY
Redis credentials if applicable
other provider secrets

Non-sensitive configuration may remain normal ECS environment variables.

Never commit secrets into:
- Git
- Dockerfile
- task-definition source
- GitHub workflow source
- .env.example

Use placeholders only.

AWS guidance recommends storing secret material in Secrets Manager or encrypted Parameter Store and granting access through ECS roles. :contentReference[oaicite:6]{index=6}

Important:
if Secrets Manager values are injected into ECS environment variables and later rotated, new tasks must be launched to pick up the new values. :contentReference[oaicite:7]{index=7}

============================================================
19. CLOUDWATCH
============================================================

Configure CloudWatch Logs for:

backend container
frontend container if useful
migration task

Create sensible log groups:

/policyflow/backend
/policyflow/frontend
/policyflow/migrations

Set retention appropriate for portfolio POC.

Do not duplicate LangSmith traces into CloudWatch unnecessarily.

CloudWatch responsibilities:

container logs
application errors
infrastructure events
health issues

LangSmith responsibilities:

AI traces
model execution
LangGraph workflow traces
token/latency metadata

============================================================
20. HEALTH AND READINESS
============================================================

Preserve:

GET /health
GET /ready

/health:
application process liveness

/ready:
dependencies such as PostgreSQL/Redis

ALB target health checks should prefer a lightweight endpoint that does not cause instability.

Decide whether:
ALB checks /health
while deployment smoke test checks /ready.

Do not make ALB continuously fail just because a non-critical observability provider is unavailable.

============================================================
21. CLOUDflare
============================================================

Target external path:

User
    ->
Cloudflare
    ->
ALB
    ->
ECS

Configure:

DNS
TLS
proxied record where applicable
basic WAF/rate protection
optional Zero Trust only if needed

Do not expose RDS/Redis through Cloudflare.

Cloudflare recommends proxying suitable DNS records and protecting the origin rather than exposing origin infrastructure unnecessarily. :contentReference[oaicite:8]{index=8}

For additional hardening, document optional Authenticated Origin Pull/mTLS with ALB, but do not make it mandatory unless implementation time permits. Cloudflare currently documents AWS ALB integration for authenticated origin pulls. :contentReference[oaicite:9]{index=9}

============================================================
22. CLOUDFLARE DNS
============================================================

Document required DNS records.

Examples:

app.example.com
-> ALB DNS

or:

policyflow.example.com
-> ALB DNS

If API uses separate hostname:

api.policyflow.example.com
-> ALB DNS

Prefer proxied Cloudflare records when compatible.

Do not hardcode real domain names into reusable infrastructure modules unless already configured.

============================================================
23. TLS
============================================================

Use HTTPS.

Possible flow:

Browser
-> Cloudflare HTTPS
-> ALB HTTPS

Preferred secure origin mode:
Cloudflare Full (strict) style setup with valid origin certificate/ACM design.

If ALB terminates TLS:
use ACM certificate.

Do not use insecure HTTP origin for final hardened deployment unless explicitly documented as a temporary POC limitation.

============================================================
24. GITHUB ACTIONS CI/CD
============================================================

Inspect current workflows.

Expected pipeline:

Pull Request:
    ->
backend tests
    ->
frontend build
    ->
OpenSpec validation
    ->
evaluation smoke tests
    ->
Docker build validation

Main branch / manual deployment:

tests
    ->
build backend image
    ->
build frontend image
    ->
AWS authentication
    ->
push to ECR
    ->
run Alembic migration task
    ->
register/update ECS task definition
    ->
deploy ECS service
    ->
wait for stability
    ->
smoke test

============================================================
25. GITHUB -> AWS AUTHENTICATION
============================================================

Prefer GitHub Actions OIDC federation to AWS rather than long-lived AWS access keys if practical.

If existing project uses secrets:
do not make destructive changes without need.

For new implementation:
prefer short-lived role assumption.

Document IAM role required by GitHub Actions.

No AWS root credentials.

No long-lived secret keys committed.

============================================================
26. CI QUALITY GATES
============================================================

Before deployment, require:

backend tests pass
frontend build passes
migration validation passes
OpenSpec validation passes
critical deterministic evaluation passes

Do not require expensive live Ragas/DeepEval evaluation on every deploy unless specifically configured.

Preserve Phase 007 split between fast CI and optional live AI evaluation.

============================================================
27. DOCKER IMAGE HARDENING
============================================================

Improve images where practical:

- minimal/slim base images;
- multi-stage builds;
- non-root runtime;
- .dockerignore;
- no source secrets;
- deterministic dependency installation;
- health support;
- no unnecessary build tools in runtime image.

Optionally scan images during CI.

Do not introduce a complex security platform.

============================================================
28. FARGATE HARDENING
============================================================

Use a current Fargate platform version.

Avoid privileged mode.

Run containers as non-root where practical.

Limit container permissions.

Use encrypted ephemeral storage defaults/configuration where appropriate.

AWS recommends Fargate security controls including encrypted ephemeral storage and minimizing task/container privileges. :contentReference[oaicite:10]{index=10}

============================================================
29. ENVIRONMENT CONFIGURATION
============================================================

Separate:

Secrets:
Secrets Manager

Non-secrets:
ECS environment variables

Examples non-secret:

APP_ENV=prod
LOG_LEVEL=INFO
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=policyflow-ai-prod
RRF_K=60
RERANK_TOP_K=5

Examples secret:

OPENAI_API_KEY
COHERE_API_KEY
LANGSMITH_API_KEY
DB password

============================================================
30. PRODUCTION CORS
============================================================

Update backend CORS configuration.

Do not allow:

*

in production unless explicitly justified.

Use configured frontend domain(s).

Example:

ALLOWED_ORIGINS=https://policyflow.example.com

Keep local development origins available only in dev config.

============================================================
31. FRONTEND API BASE URL
============================================================

Ensure production frontend resolves backend correctly.

Possible:

VITE_API_BASE_URL=https://policyflow.example.com/api

or separate API hostname.

Remember Vite variables are compiled into the frontend bundle.

Do not expect runtime server environment variables to automatically replace already-built Vite values unless current container solution explicitly implements runtime substitution.

============================================================
32. DATABASE CONNECTION MANAGEMENT
============================================================

Review SQLAlchemy pooling for RDS.

Use sensible pool settings.

Do not create uncontrolled DB connections per request.

Account for multiple ECS tasks.

Keep pool sizes modest for POC.

Do not over-provision RDS solely to handle poor connection configuration.

============================================================
33. REDIS CONNECTION MANAGEMENT
============================================================

Use pooled/reused Redis connections.

Define:

connect timeout
read timeout
retry behavior where existing client supports it

Do not block indefinitely.

============================================================
34. EXTERNAL PROVIDER EGRESS
============================================================

Backend requires outbound HTTPS to:

OpenAI
Cohere if configured
LangSmith

Ensure ECS network path supports outbound HTTPS.

If private ECS subnets require NAT, account for this.

Cost-conscious alternative architecture must be explicitly documented if avoiding NAT.

Do not silently create an architecture where backend cannot reach model providers.

============================================================
35. COST CONTROL
============================================================

This is a portfolio POC.

Keep costs bounded.

Use:
- one environment;
- one AWS region;
- small ECS desired counts;
- modest RDS instance;
- modest Redis;
- reasonable log retention;
- one ALB;
- one RDS where architecture allows.

Avoid:
- EKS;
- multi-region;
- provisioned excess capacity;
- NAT gateways without acknowledging their cost;
- unnecessary duplicate databases.

Document estimated major cost drivers.

============================================================
36. DEPLOYMENT CONFIGURATION STRUCTURE
============================================================

Use current repo structure.

Expected logical area:

infrastructure/aws/

Possible subdirectories:

network/
ecs/
rds/
redis/
s3/
secrets/
iam/
alb/

Do not reorganize the entire repository unless needed.

============================================================
37. BACKEND DEPLOYMENT SEQUENCE
============================================================

Expected:

1. infrastructure available
2. ECR repository available
3. image built
4. image pushed
5. migration task launched
6. migrations succeed
7. ECS service updated
8. ALB health passes
9. /ready passes
10. smoke tests run

If migration fails:
do not deploy incompatible backend.

============================================================
38. FRONTEND DEPLOYMENT SEQUENCE
============================================================

Expected:

1. build production React bundle
2. build frontend image
3. push to ECR
4. update ECS frontend service
5. wait for target health
6. request homepage
7. verify API connectivity

============================================================
39. SMOKE TESTS
============================================================

Create deployment smoke tests.

At minimum:

GET /
-> frontend accessible

GET /health
-> 200

GET /ready
-> PostgreSQL and Redis ready

Policy Q&A smoke:
"What is the maximum hotel reimbursement allowed for domestic travel?"
-> grounded response or safely configured test mode

Expense assessment:
known synthetic case

Do not require destructive HITL flow for every deployment smoke test.

============================================================
40. MIGRATION SMOKE
============================================================

Verify:

Alembic current == head

Verify pgvector extension.

Verify required schemas:

app
rag
audit
checkpoint logical store as implemented

Do not expose schema credentials/results publicly.

============================================================
41. ROLLBACK STRATEGY
============================================================

Document rollback.

Application rollback:

previous ECS task definition revision
+
previous ECR image SHA/tag

Database rollback:
do NOT automatically downgrade irreversible migrations.

Prefer backward-compatible migrations.

If deployment fails after migration:
application rollback should work with migrated schema where possible.

Explain this clearly.

============================================================
42. DEPLOYMENT FAILURE HANDLING
============================================================

Handle:

ECR push failure
migration failure
ECS service unstable
ALB target unhealthy
RDS connectivity failure
Redis failure
Secrets missing
provider API unavailable

Deployment pipeline should fail visibly.

Do not declare deployment success only because image push succeeded.

============================================================
43. ECS DEPLOYMENT VALIDATION
============================================================

After deployment:

wait for ECS service stability.

Verify:
running task count == desired task count

Verify ALB target:
healthy

Verify CloudWatch:
no startup crash loop

Verify backend:
health/ready endpoints

============================================================
44. SECRET VALIDATION
============================================================

At deployment time, verify required secret references exist.

Do NOT print actual secret values.

Safe checks:

secret ARN exists
task role has access
task starts successfully

Never echo provider tokens in GitHub logs.

============================================================
45. IAM LEAST PRIVILEGE
============================================================

GitHub deployment role should have only deployment-required actions.

Backend task role should have only runtime-required actions.

Examples:

S3 read policy bucket
Secrets access if runtime retrieval is used

Do not attach:
AdministratorAccess

unless purely temporary/manual and explicitly documented outside committed IaC.

============================================================
46. S3 POLICY INGESTION
============================================================

If the backend already supports local policy ingestion, do not rewrite it unnecessarily.

For AWS deployment optionally allow:

S3
    ->
policy ingestion process

Synthetic Markdown policy files may be uploaded to S3.

Ingestion still writes authoritative RAG chunks to PostgreSQL.

S3 is source object storage, not vector store.

============================================================
47. LOGGING
============================================================

Container logs should be structured where already supported.

Include:

timestamp
level
request_id
thread_id
service
message

Do not log:

OpenAI key
LangSmith key
DB password
authorization headers

Preserve Phase 007 redaction behavior.

============================================================
48. CLOUDWATCH ALARMS
============================================================

For the POC, optional/basic alarms:

ECS task unhealthy
ALB unhealthy hosts
5xx spike
RDS CPU/storage
Redis health

Do not implement a huge monitoring stack.

Document recommended alarms if full implementation is out of scope.

============================================================
49. HIGH AVAILABILITY
============================================================

Because FRD allows one environment and low POC traffic, do not over-engineer.

ALB naturally spans multiple AZs.

ECS may remain desired_count=1 initially.

RDS may use a single-AZ cost-conscious setup for demo if source design permits.

Clearly document that production regulated deployment would require stronger HA/DR.

The FRD explicitly allows one AWS region and one environment for the public demo. :contentReference[oaicite:11]{index=11}

============================================================
50. CLOUDFLARE ORIGIN HARDENING
============================================================

At minimum:

proxied DNS
HTTPS
avoid direct public backend exposure

Optional:
restrict origin to Cloudflare ranges
authenticated origin pulls/mTLS

Do not accidentally lock GitHub/deployment health verification out unless health checks use direct ALB paths.

============================================================
51. README DEPLOYMENT DOCUMENTATION
============================================================

Update README or create:

docs/deployment/aws-deployment.md

Include:

architecture
prerequisites
AWS services used
environment variables
secrets
initial deploy
database migration
GitHub Actions
Cloudflare configuration
smoke testing
rollback
cleanup
cost notes
known limitations

============================================================
52. CLEANUP / DESTROY
============================================================

Because this is a personal portfolio POC, document how to stop costs.

Examples:

scale ECS services to 0 where applicable
destroy IaC resources if disposable
delete unused ALB/NAT resources
snapshot/delete RDS as intended
remove Redis
retain/delete ECR images
retain/delete S3 artifacts carefully

If IaC supports destroy:
document command.

Do not automatically destroy resources.

============================================================
53. ENVIRONMENT NAMES
============================================================

Suggested:

dev
or
demo

Avoid overbuilding:

dev
qa
uat
prod

for a single-engineer POC unless current infrastructure already has them.

============================================================
54. GITHUB ACTIONS WORKFLOW
============================================================

Suggested file:

.github/workflows/deploy-aws.yml

Trigger:

workflow_dispatch

and optionally:
push to main

Recommended jobs:

validate
test
build
push
migrate
deploy
smoke-test

Use concurrency protection to avoid two simultaneous deployments.

============================================================
55. CI/CD ARTIFACT TRACEABILITY
============================================================

Capture:

git SHA
backend image tag
frontend image tag
ECS task definition revision
deployment timestamp

This makes rollback/debugging explainable.

============================================================
56. DEPLOYMENT SECURITY CHECKLIST
============================================================

Validate:

[ ] no DB public endpoint
[ ] no Redis public endpoint
[ ] no secrets committed
[ ] no provider keys in frontend
[ ] ECS tasks behind ALB
[ ] IAM least privilege
[ ] production CORS restricted
[ ] HTTPS enabled
[ ] S3 public access blocked
[ ] encrypted persistence enabled
[ ] image tags traceable
[ ] logs redacted
[ ] health checks configured

============================================================
57. TESTING
============================================================

Add/update tests where feasible.

LOCAL:
backend tests
frontend build
Docker build

INFRA:
IaC validate
IaC format/lint if applicable

DEPLOYMENT:
health check
readiness check
frontend HTTP test
API test
known Policy Q&A smoke
known expense assessment smoke

Do not depend on manual browser testing alone.

============================================================
58. REQUIRED COMMANDS
============================================================

Use tooling discovered in repository.

Examples:

Backend:

python -m pytest backend/tests -v

Frontend:

npm ci
npm run build

Docker:

docker build -t policyflow-backend ./backend
docker build -t policyflow-frontend ./frontend

Compose regression:

docker compose up -d
docker compose ps

OpenSpec:

openspec validate

Infrastructure if Terraform:

terraform fmt -check
terraform validate
terraform plan

If CDK:

cdk synth
cdk diff

Do not run destructive apply automatically unless user explicitly intends real deployment.

============================================================
59. IMPORTANT: DO NOT CREATE REAL CLOUD RESOURCES WITHOUT CONFIRMATION
============================================================

During implementation:

generate infrastructure/configuration/code.

Validate syntax and plans.

Do not automatically execute:

terraform apply
cdk deploy
aws cloudformation deploy
resource deletion

unless the user explicitly requests real AWS deployment and credentials are configured.

The implementation should prepare deployment safely.

============================================================
60. DEPLOYMENT HARDENING
============================================================

Review application configuration for cloud runtime:

CORS
trusted hosts
timeouts
DB pooling
Redis timeouts
external provider timeouts
log levels
debug=false
secret handling

Do not change business logic.

============================================================
61. DEFINITION OF DONE ARCHITECTURE
============================================================

Final architecture:

                         Internet
                            |
                            v
                       Cloudflare
                            |
                            v
                         AWS ALB
                       /         \
                      /           \
                     v             v
              React Frontend   FastAPI Backend
                  ECS              ECS
                Fargate          Fargate
                                  |
                 +----------------+----------------+
                 |                |                |
                 v                v                v
               RDS          ElastiCache           S3
        PostgreSQL+pgvector     Redis         Policy Docs
                 |
                 +--> app schema
                 +--> rag schema
                 +--> audit schema
                 +--> LangGraph checkpoints

FastAPI
  |
  +--> OpenAI/Cohere
  |
  +--> LangSmith

Secrets:
Secrets Manager

Images:
GitHub Actions -> ECR -> ECS

Logs:
ECS -> CloudWatch

============================================================
62. IMPLEMENTATION ORDER
============================================================

Implement incrementally:

Step 1
Inspect existing deployment/infrastructure code.

Step 2
Create/update OpenSpec 008 artifacts.

Step 3
Validate OpenSpec.

Step 4
Harden backend Docker image.

Step 5
Harden frontend Docker image.

Step 6
Finalize production configuration.

Step 7
Define VPC/subnets/security groups.

Step 8
Define ECR.

Step 9
Define RDS.

Step 10
Validate pgvector setup.

Step 11
Define ElastiCache.

Step 12
Define S3.

Step 13
Define Secrets Manager references.

Step 14
Define IAM roles.

Step 15
Define ECS cluster/task definitions.

Step 16
Define ECS services.

Step 17
Define ALB/target groups/listeners.

Step 18
Configure CloudWatch logs.

Step 19
Define migration task.

Step 20
Implement GitHub Actions build/push.

Step 21
Implement migration stage.

Step 22
Implement ECS deployment stage.

Step 23
Implement deployment smoke tests.

Step 24
Document Cloudflare DNS/TLS.

Step 25
Add deployment rollback procedure.

Step 26
Add cost/cleanup documentation.

Step 27
Run local test suite.

Step 28
Run frontend build.

Step 29
Build Docker images.

Step 30
Validate IaC.

Step 31
Generate infrastructure plan/diff.

Step 32
Validate GitHub Actions syntax.

Step 33
Validate OpenSpec.

Step 34
Update tasks.md accurately.

STOP.

Do not execute destructive deployment commands without explicit approval.

============================================================
63. ACCEPTANCE CRITERIA
============================================================

Phase 008 is complete only when:

[ ] OpenSpec 008 proposal/design/spec/tasks validate

[ ] backend production Docker image builds

[ ] frontend production Docker image builds

[ ] images are ready for ECR

[ ] ECS/Fargate infrastructure defined

[ ] separate frontend/backend ECS services defined

[ ] ALB routing defined

[ ] RDS PostgreSQL defined

[ ] RDS private access enforced

[ ] pgvector migration validated

[ ] ElastiCache defined

[ ] Redis private access enforced

[ ] S3 bucket defined securely

[ ] Secrets Manager integrated

[ ] task execution role uses least privilege

[ ] task role uses least privilege

[ ] CloudWatch logs configured

[ ] health checks configured

[ ] readiness smoke test defined

[ ] production CORS configured

[ ] frontend API URL production behavior defined

[ ] GitHub Actions builds backend image

[ ] GitHub Actions builds frontend image

[ ] GitHub Actions pushes to ECR

[ ] database migration deployment step exists

[ ] ECS service deployment step exists

[ ] deployment waits for service stability

[ ] smoke test stage exists

[ ] rollback documented

[ ] Cloudflare DNS/TLS documented

[ ] no secrets committed

[ ] no DB/Redis public exposure

[ ] backend tests pass

[ ] frontend build passes

[ ] Docker builds pass

[ ] IaC validation passes

[ ] OpenSpec tasks match actual state

============================================================
64. PORTFOLIO DEMO VALIDATION
============================================================

Once deployed, the intended demo should support:

Scenario 1:
Policy Q&A

"What is the maximum domestic hotel reimbursement?"

-> request through Cloudflare
-> ALB
-> ECS backend
-> RDS hybrid retrieval
-> Model Gateway
-> answer with citation

Scenario 2:
Expense assessment

Hotel INR 9500
Domestic
Receipt available

-> NEEDS_REVIEW

Scenario 3:
Exception flow

employee submits justification
-> LangGraph interrupt
-> PostgreSQL checkpoint
-> reviewer action
-> same thread resumes
-> final result

Scenario 4:
Observability

open LangSmith
-> locate trace by request/thread
-> inspect retrieval/model/decision spans

CloudWatch
-> inspect ECS application logs

============================================================
65. INTERVIEW EXPLANATION
============================================================

The completed architecture should allow this explanation:

"PolicyFlow AI is packaged as frontend and backend containers and deployed on ECS/Fargate. Cloudflare protects and fronts the public endpoint, which routes through an AWS Application Load Balancer. The backend uses RDS PostgreSQL with pgvector for business state, RAG, audit data, and LangGraph checkpoint persistence, while ElastiCache Redis handles only transient coordination. S3 stores source policy documents, Secrets Manager stores runtime credentials, ECR stores immutable container images, GitHub Actions performs CI/CD, CloudWatch handles infrastructure logs, and LangSmith remains the AI-specific tracing layer."

============================================================
66. FINAL IMPLEMENTATION REPORT
============================================================

When Phase 008 implementation is complete, provide:

1. OpenSpec files created/modified
2. Docker changes
3. infrastructure files created/modified
4. VPC/network configuration
5. ECS configuration
6. ALB configuration
7. RDS configuration
8. Redis configuration
9. S3 configuration
10. Secrets Manager configuration
11. IAM roles/policies
12. CloudWatch changes
13. GitHub Actions changes
14. migration deployment strategy
15. Cloudflare instructions
16. CORS/environment changes
17. smoke tests
18. rollback procedure
19. cost considerations
20. cleanup instructions
21. commands executed
22. backend test results
23. frontend build results
24. Docker build results
25. IaC validation/plan result
26. OpenSpec validation result
27. unresolved issues
28. POC limitations
29. concise end-to-end deployment flow

Do not merely say:
"Phase 008 implemented."

Show actual validation evidence.

STOP after Phase 008.
This is the final planned OpenSpec implementation phase.

============================================================
67. PHASE 008 IMPLEMENTATION STATUS AND FILE INVENTORY
============================================================

Status:
- OpenSpec apply implementation completed locally.
- No Terraform apply, AWS resource creation, Cloudflare DNS change, secret
  population, or production deployment was executed.
- Real cloud validation remains an operator-controlled post-apply gate.

OpenSpec:
- openspec/changes/008-aws-deployment-hardening/proposal.md
- openspec/changes/008-aws-deployment-hardening/design.md
- openspec/changes/008-aws-deployment-hardening/tasks.md
- openspec/changes/008-aws-deployment-hardening/specs/aws-deployment-hardening/spec.md

Containers and runtime:
- .dockerignore
- .gitignore
- backend/Dockerfile
- backend/requirements-runtime.txt
- backend/app/core/config.py
- backend/app/core/security.py
- backend/app/db/session.py
- backend/app/cache/redis_client.py
- backend/app/main.py
- backend/tests/test_deployment_config.py
- frontend/.dockerignore
- frontend/Dockerfile
- frontend/nginx.conf
- frontend/src/api/client.ts
- docker-compose.yml
- scripts/deployment_smoke.py
- tests/unit/test_deployment_smoke.py

Infrastructure:
- infrastructure/terraform/backend.tf
- infrastructure/terraform/versions.tf
- infrastructure/terraform/providers.tf
- infrastructure/terraform/variables.tf
- infrastructure/terraform/locals.tf
- infrastructure/terraform/network.tf
- infrastructure/terraform/security-groups.tf
- infrastructure/terraform/ecr.tf
- infrastructure/terraform/rds.tf
- infrastructure/terraform/elasticache.tf
- infrastructure/terraform/s3.tf
- infrastructure/terraform/secrets.tf
- infrastructure/terraform/iam.tf
- infrastructure/terraform/cloudwatch.tf
- infrastructure/terraform/alb.tf
- infrastructure/terraform/ecs.tf
- infrastructure/terraform/outputs.tf
- infrastructure/terraform/terraform.tfvars.example
- infrastructure/terraform/.terraform.lock.hcl
- infrastructure/aws/alb/README.md
- infrastructure/aws/ecs/README.md
- infrastructure/aws/rds/README.md
- infrastructure/aws/redis/README.md
- infrastructure/aws/secrets/README.md
- infrastructure/cloudflare/README.md
- tests/unit/test_aws_iac.py

CI/CD and operations:
- .github/workflows/ci.yml
- .github/workflows/deploy-aws.yml
- docs/aws-deployment.md
- docs/phase-008-implementation-report.md
- docs/local-validation.md
- README.md
- Makefile

The above inventory is Phase 008-specific. Generated Terraform provider files,
state, plans, environment files, credentials, and live evaluation reports are
excluded from publication.
