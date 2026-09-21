resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-redis"
  subnet_ids = aws_subnet.database[*].id
}
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "PolicyFlow transient coordination cache"
  engine                     = "redis"
  node_type                  = var.redis_node_type
  port                       = 6379
  num_cache_clusters         = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  snapshot_retention_limit   = 0
  apply_immediately          = false
}
