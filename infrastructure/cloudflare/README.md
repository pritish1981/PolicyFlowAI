# Cloudflare Edge

Create a proxied CNAME from the chosen PolicyFlow hostname to the Terraform
alb_dns_name output. Use Full (strict) TLS with an ACM certificate on the ALB,
enable reasonable managed WAF/rate controls, and bypass HTML caching for API and
health paths. Never publish RDS or Redis.

Cloudflare IP allow-listing or authenticated origin pulls may be added when
their certificate/IP lifecycle has an owner; neither is required for the
cost-conscious initial POC. See docs/aws-deployment.md for full instructions.
