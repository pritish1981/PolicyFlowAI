# ElastiCache Redis

Terraform defines one private, encrypted Redis replication group node in the
isolated database subnets. Only ECS tasks can reach port 6379. Use a rediss URL
in Secrets Manager. Redis remains transient coordination/cache state and never
becomes the source of business or checkpoint truth.
