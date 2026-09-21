resource "aws_ecs_cluster" "main" {
  name = local.name_prefix
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

locals {
  backend_environment = [
    { name = "APP_NAME", value = "PolicyFlow AI" },
    { name = "APP_ENV", value = var.environment },
    { name = "CORS_ORIGINS", value = "https://${var.domain_name}" },
    { name = "TRUSTED_HOSTS", value = var.domain_name },
    { name = "ENABLE_API_DOCS", value = "false" },
    { name = "LOG_LEVEL", value = "INFO" },
    { name = "S3_BUCKET", value = aws_s3_bucket.artifacts.id },
    { name = "LANGSMITH_TRACING", value = "true" }
  ]
  backend_secrets = [for name, secret in aws_secretsmanager_secret.backend : {
    name      = name
    valueFrom = secret.arn
  }]
  backend_log_configuration = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.backend.name
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "backend"
    }
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.backend_cpu)
  memory                   = tostring(var.backend_memory)
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name         = "backend"
    image        = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
    essential    = true
    environment  = local.backend_environment
    secrets      = local.backend_secrets
    portMappings = [{ containerPort = 8000, hostPort = 8000, protocol = "tcp" }]
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
    logConfiguration = local.backend_log_configuration
  }])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.frontend_cpu)
  memory                   = tostring(var.frontend_memory)
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.frontend_task.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name         = "frontend"
    image        = "${aws_ecr_repository.frontend.repository_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8080, hostPort = 8080, protocol = "tcp" }]
    healthCheck = {
      command     = ["CMD-SHELL", "wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 10
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.frontend.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "frontend"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name_prefix}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.backend_cpu)
  memory                   = tostring(var.backend_memory)
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name        = "migration"
    image       = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
    essential   = true
    command     = ["python", "-m", "alembic", "upgrade", "head"]
    environment = local.backend_environment
    secrets     = local.backend_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.migrations.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "migration"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name                               = "${local.name_prefix}-backend"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = aws_subnet.application[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener_rule.backend_api]
}

resource "aws_ecs_service" "frontend" {
  name                               = "${local.name_prefix}-frontend"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.frontend.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 45
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = aws_subnet.application[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 8080
  }
  depends_on = [aws_lb_listener.https]
}
