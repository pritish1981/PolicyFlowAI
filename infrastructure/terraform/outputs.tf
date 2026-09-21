output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Cloudflare proxied CNAME target."
}

output "application_url" {
  value       = "https://${var.domain_name}"
  description = "Expected public PolicyFlow URL after Cloudflare DNS configuration."
}

output "ecr_repository_urls" {
  value = {
    backend  = aws_ecr_repository.backend.repository_url
    frontend = aws_ecr_repository.frontend.repository_url
  }
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_names" {
  value = {
    backend  = aws_ecs_service.backend.name
    frontend = aws_ecs_service.frontend.name
  }
}

output "task_definition_arns" {
  value = {
    backend   = aws_ecs_task_definition.backend.arn
    frontend  = aws_ecs_task_definition.frontend.arn
    migration = aws_ecs_task_definition.migration.arn
  }
}

output "application_subnet_ids" {
  value = aws_subnet.application[*].id
}

output "ecs_security_group_id" {
  value = aws_security_group.ecs.id
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Private RDS endpoint; credentials are not exposed."
}

output "redis_primary_endpoint" {
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "Private TLS Redis endpoint."
}

output "artifact_bucket_name" {
  value = aws_s3_bucket.artifacts.id
}

output "backend_secret_arns" {
  value       = { for name, secret in aws_secretsmanager_secret.backend : name => secret.arn }
  description = "Secret containers that must be populated out of band."
}
