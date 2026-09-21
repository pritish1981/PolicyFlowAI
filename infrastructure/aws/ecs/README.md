# ECS/Fargate

Terraform defines one private frontend service, one private backend service, and
a non-service migration task. Services use SHA-tagged ECR images, CloudWatch
logs, deployment circuit breakers, ALB target groups, and no public IPs.

GitHub Actions runs exactly one migration task before updating either service.
See docs/aws-deployment.md for required GitHub variables and rollback.
