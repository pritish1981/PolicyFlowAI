# RDS PostgreSQL

The POC uses one encrypted, private PostgreSQL 16 instance in isolated database
subnets. It is single-AZ and small by default for cost control. Only the ECS
security group can reach port 5432. Alembic enables pgvector and maintains app,
rag, audit, and checkpoint logical separation.

The generated RDS master credential is not an application connection string.
Populate the DATABASE_URL secret out of band and verify pgvector after migration
as documented in docs/aws-deployment.md.
