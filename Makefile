up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

backend:
	cd backend && uvicorn app.main:app --reload

test:
	pytest -q tests backend/tests

docker-build:
	docker build -f backend/Dockerfile -t policyflow-backend:local .
	docker build -t policyflow-frontend:local frontend

terraform-check:
	terraform -chdir=infrastructure/terraform fmt -check
	terraform -chdir=infrastructure/terraform init -backend=false
	terraform -chdir=infrastructure/terraform validate

openspec-check:
	npx -y @fission-ai/openspec@1.10.0 validate --all --strict

deployment-smoke:
	python scripts/deployment_smoke.py --base-url $(BASE_URL)
