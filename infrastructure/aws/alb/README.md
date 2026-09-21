# Application Load Balancer

Terraform in ../../terraform/alb.tf defines a public ALB across two public
subnets. Port 80 redirects to HTTPS. The ACM-backed 443 listener sends the
default route to frontend port 8080 and API, health, readiness, docs, and
OpenAPI paths to backend port 8000. Target health uses /healthz for frontend and
/health for backend; /ready is reserved for deployment smoke validation.

See docs/aws-deployment.md for Cloudflare, TLS, validation, and rollback.
