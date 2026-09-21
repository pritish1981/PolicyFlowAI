resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db"
  subnet_ids = aws_subnet.database[*].id
}
resource "aws_db_instance" "postgres" {
  identifier                      = "${local.name_prefix}-postgres"
  engine                          = "postgres"
  engine_version                  = var.db_engine_version
  instance_class                  = var.db_instance_class
  allocated_storage               = var.db_allocated_storage
  max_allocated_storage           = 100
  storage_type                    = "gp3"
  storage_encrypted               = true
  db_name                         = var.db_name
  username                        = var.db_username
  manage_master_user_password     = true
  port                            = 5432
  publicly_accessible             = false
  multi_az                        = false
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  backup_retention_period         = var.db_backup_retention_days
  copy_tags_to_snapshot           = true
  deletion_protection             = var.db_deletion_protection
  skip_final_snapshot             = var.skip_final_snapshot
  final_snapshot_identifier       = var.skip_final_snapshot ? null : "${local.name_prefix}-final"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  auto_minor_version_upgrade      = true
  apply_immediately               = false
}
