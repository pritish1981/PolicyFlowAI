resource "aws_cloudwatch_log_group" "backend" {
  name              = "/${local.name_prefix}/backend"
  retention_in_days = var.cloudwatch_retention_days
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/${local.name_prefix}/frontend"
  retention_in_days = var.cloudwatch_retention_days
}

resource "aws_cloudwatch_log_group" "migrations" {
  name              = "/${local.name_prefix}/migrations"
  retention_in_days = var.cloudwatch_retention_days
}
