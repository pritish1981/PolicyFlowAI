variable "aws_region" {
  description = "AWS region for the PolicyFlow POC."
  type        = string
  default     = "ap-south-1"
}
variable "project_name" {
  description = "Lowercase project identifier used in resource names."
  type        = string
  default     = "policyflow"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,23}$", var.project_name))
    error_message = "project_name must be 3-24 lowercase alphanumeric or hyphen characters."
  }
}

variable "environment" {
  description = "Deployment environment identifier."
  type        = string
  default     = "poc"
  validation {
    condition     = contains(["poc", "dev", "staging", "prod"], var.environment)
    error_message = "environment must be poc, dev, staging, or prod."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "IPv4 CIDR for the VPC."
  default     = "10.42.0.0/16"
}

variable "domain_name" {
  type        = string
  description = "Public application hostname managed in Cloudflare."
}

variable "certificate_arn" {
  type        = string
  description = "Validated ACM certificate ARN for domain_name in the deployment region."
  validation {
    condition     = startswith(var.certificate_arn, "arn:aws:acm:")
    error_message = "certificate_arn must be an ACM ARN."
  }
}

variable "image_tag" {
  type        = string
  description = "Immutable Git SHA image tag deployed to both services."
  validation {
    condition     = can(regex("^[0-9a-f]{7,40}$", var.image_tag))
    error_message = "image_tag must be a 7-40 character lowercase Git SHA."
  }
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "desired_count" {
  type    = number
  default = 1
  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 4
    error_message = "desired_count must remain between 1 and 4 for this POC."
  }
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_engine_version" {
  type    = string
  default = "16.3"
}

variable "db_name" {
  type    = string
  default = "policyflow"
}

variable "db_username" {
  type    = string
  default = "policyflow_admin"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "db_backup_retention_days" {
  type    = number
  default = 1
}

variable "db_deletion_protection" {
  type    = bool
  default = false
}

variable "skip_final_snapshot" {
  type    = bool
  default = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "cloudwatch_retention_days" {
  type    = number
  default = 14
}

variable "alb_deletion_protection" {
  type    = bool
  default = false
}

variable "force_delete_artifact_bucket" {
  type    = bool
  default = false
}
