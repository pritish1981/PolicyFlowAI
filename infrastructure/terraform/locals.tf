locals {
  name_prefix        = "${var.project_name}-${var.environment}"
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  common_tags = {
    Project     = "PolicyFlow-AI"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  backend_secret_names = toset([
    "DATABASE_URL",
    "REDIS_URL",
    "OPENAI_API_KEY",
    "COHERE_API_KEY",
    "LANGSMITH_API_KEY",
    "POLICY_ADMIN_TOKEN"
  ])
}
