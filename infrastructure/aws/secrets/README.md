# Secrets Manager and IAM

Terraform creates named secret containers without secret versions or values.
Operators populate database, Redis, provider, tracing, and admin-token values
out of band. ECS receives references through a dedicated execution role.

The backend task role has only scoped access to the PolicyFlow S3 bucket. The
frontend task role has no application AWS permissions. Rotate secrets privately
and force a new backend deployment to load them.
