## Purpose

Define the observable security, availability, delivery, migration, and operational behavior required to deploy PolicyFlow AI as a cost-conscious AWS portfolio POC behind Cloudflare.

## ADDED Requirements

### Requirement: Production containers
The system SHALL provide independently buildable production images for the React frontend and FastAPI backend, SHALL run application processes without root privileges where supported, SHALL exclude local secrets from image layers, and SHALL expose lightweight health endpoints.

#### Scenario: Images build without private credentials
- **WHEN** both production images are built from a clean checkout without provider API keys
- **THEN** each build completes and neither image requires or contains a committed environment file or secret value

#### Scenario: Runtime health checks
- **WHEN** a running frontend or backend task receives its configured liveness request
- **THEN** it returns a successful response without contacting an external AI or observability provider

### Requirement: Edge and load-balancer ingress
The deployed system SHALL receive public traffic through Cloudflare and an HTTPS AWS Application Load Balancer, SHALL route frontend and backend paths to separate target groups, and SHALL redirect plaintext HTTP to HTTPS.

#### Scenario: Browser request routing
- **WHEN** a user accesses the configured application hostname through Cloudflare
- **THEN** frontend paths reach the frontend service and API and backend health paths reach the backend service over the ALB HTTPS listener

#### Scenario: Plaintext request
- **WHEN** a client sends an HTTP request to the ALB listener
- **THEN** the ALB redirects the request to HTTPS

### Requirement: Private application dependencies
The system SHALL keep RDS PostgreSQL and ElastiCache Redis inaccessible from the public internet, SHALL admit their service ports only from the ECS task security group, and SHALL admit ECS application ports only from the ALB security group.

#### Scenario: Database network exposure
- **WHEN** the deployed security groups and subnet attributes are inspected
- **THEN** PostgreSQL and Redis have no public address or internet-wide ingress and accept traffic only from application tasks

### Requirement: Durable and transient state boundaries
The deployment SHALL use RDS PostgreSQL with pgvector for authoritative application, RAG, audit, and logically separated checkpoint data, SHALL use Redis only for transient coordination, and SHALL use S3 only for policy sources and optional artifacts rather than authoritative business records.

#### Scenario: PostgreSQL initialization
- **WHEN** the migration task runs against a new supported RDS PostgreSQL instance
- **THEN** the vector extension and required logical schemas and tables are created before the backend service is deployed

#### Scenario: Redis unavailable
- **WHEN** Redis is temporarily unavailable
- **THEN** readiness reports the dependency failure and no authoritative business or checkpoint record is reconstructed from Redis

### Requirement: Secure configuration and secrets
The deployment SHALL store sensitive provider and connection values in AWS Secrets Manager, SHALL inject only referenced secrets into backend tasks, SHALL keep frontend configuration non-sensitive, and SHALL separate the ECS execution role from the backend application task role using least privilege.

#### Scenario: Task definition inspection
- **WHEN** the rendered task definitions and IAM policies are reviewed
- **THEN** secret values are absent, secret references are explicit, the execution role has only startup permissions, and the application role has only required S3 access

#### Scenario: Secret rotation
- **WHEN** a Secrets Manager value is rotated
- **THEN** operations documentation requires a new backend task deployment before the rotated value is considered active

### Requirement: Traceable image delivery
The delivery pipeline SHALL authenticate to AWS through GitHub OIDC, SHALL publish frontend and backend images to separate ECR repositories with immutable Git SHA tags, and SHALL deploy the selected SHA rather than relying only on a mutable tag.

#### Scenario: Main-branch deployment
- **WHEN** an authorized deployment workflow runs for a tested commit
- **THEN** it builds and pushes both SHA-tagged images and registers task revisions that reference that SHA

#### Scenario: Pull request validation
- **WHEN** a pull request changes application, infrastructure, or deployment files
- **THEN** CI tests the backend, tests and builds the frontend, validates OpenSpec and Terraform, and validates both container builds without modifying AWS resources

### Requirement: Serialized database migration
The deployment SHALL execute Alembic migration as one dedicated ECS task before updating the backend service and SHALL fail the deployment when that task fails.

#### Scenario: Successful migration
- **WHEN** a deployment targets a reachable compatible database
- **THEN** exactly one migration task upgrades to the current Alembic head and exits successfully before service rollout begins

#### Scenario: Failed migration
- **WHEN** the migration task exits unsuccessfully or times out
- **THEN** the pipeline stops without updating either ECS service

### Requirement: Health, readiness, and deployment smoke checks
The ALB SHALL use lightweight liveness checks, while deployment validation SHALL verify backend readiness and public application availability without requiring OpenAI, Cohere, or LangSmith to be reachable.

#### Scenario: Stable rollout
- **WHEN** updated ECS services reach steady state
- **THEN** the deployment verifies the public frontend, backend health, and backend readiness endpoints and reports a clear pass or failure

#### Scenario: Non-critical provider outage
- **WHEN** an AI model or LangSmith is unavailable but the application process and required state stores are healthy
- **THEN** ALB liveness remains healthy and the provider outage does not trigger container replacement

### Requirement: Operational logging
The deployment SHALL send backend, frontend, and migration container logs to separate encrypted CloudWatch log groups with configurable finite retention, while LangSmith remains responsible only for AI-specific traces.

#### Scenario: Container failure diagnosis
- **WHEN** a task or migration fails
- **THEN** operators can locate its structured operational logs in the corresponding CloudWatch log group without relying on LangSmith

### Requirement: Repeatable rollback
The deployment SHALL retain traceable task definition revisions and image tags and SHALL document how to restore the previous service task definitions without rolling database schema down automatically.

#### Scenario: Post-deployment smoke failure
- **WHEN** smoke validation fails after a service update
- **THEN** the workflow or operator can restore the captured previous frontend and backend task definition revisions and wait for service stability

### Requirement: Cost-conscious lifecycle
The infrastructure SHALL default to POC-sized configurable resources, SHALL avoid Kubernetes and unnecessary managed services, and SHALL document recurring cost drivers and a dependency-aware cleanup procedure.

#### Scenario: Default plan review
- **WHEN** the default Terraform plan is reviewed
- **THEN** it contains one small backend task, one small frontend task, a single-AZ database, one small Redis node, and one shared NAT gateway unless explicitly overridden

#### Scenario: Cleanup
- **WHEN** the owner ends the demo
- **THEN** documentation identifies retained data and provides an ordered destroy procedure that prevents accidental loss unless explicitly confirmed

### Requirement: Existing authority semantics remain unchanged
The deployment SHALL preserve the Phase 001-007 API, policy evidence, deterministic expense decision, citation, model-governance, checkpoint, and human-authorization boundaries.

#### Scenario: Deployment regression validation
- **WHEN** the complete backend and frontend regression suites run against the hardened packaging
- **THEN** existing policy Q&A, expense assessment, HITL, gateway, guardrail, and observability behavior remains unchanged
