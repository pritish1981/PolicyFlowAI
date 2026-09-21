resource "aws_secretsmanager_secret" "backend" {
  for_each                = local.backend_secret_names
  name                    = "/${local.name_prefix}/${each.value}"
  recovery_window_in_days = 7
  description             = "Runtime secret reference for PolicyFlow ${each.value}; value populated out of band"
}
