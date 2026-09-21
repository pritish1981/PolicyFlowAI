from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "infrastructure" / "terraform"


def _read(name: str) -> str:
    return (TF / name).read_text(encoding="utf-8")


def test_stateful_services_are_private_and_encrypted() -> None:
    rds = _read("rds.tf")
    redis = _read("elasticache.tf")
    s3 = _read("s3.tf")
    network = _read("network.tf")

    assert re.search(r"publicly_accessible\s*=\s*false", rds)
    assert re.search(r"storage_encrypted\s*=\s*true", rds)
    assert re.search(r"transit_encryption_enabled\s*=\s*true", redis)
    assert re.search(r"at_rest_encryption_enabled\s*=\s*true", redis)
    assert re.search(r"block_public_policy\s*=\s*true", s3)
    assert 'resource "aws_route_table" "database"' in network
    database_route = network.split('resource "aws_route_table" "database"', 1)[1].split(
        "resource", 1
    )[0]
    assert "0.0.0.0/0" not in database_route


def test_security_groups_do_not_expose_postgres_or_redis_publicly() -> None:
    security = _read("security-groups.tf")

    for block_name in ("rds_from_ecs", "redis_from_ecs"):
        block = security.split(f'"{block_name}"', 1)[1].split("resource", 1)[0]
        assert "referenced_security_group_id = aws_security_group.ecs.id" in block
        assert "0.0.0.0/0" not in block


def test_ecs_services_are_private_and_migrations_are_not_a_service() -> None:
    ecs = _read("ecs.tf")

    assert ecs.count("assign_public_ip = false") == 2
    assert 'resource "aws_ecs_task_definition" "migration"' in ecs
    assert 'resource "aws_ecs_service" "migration"' not in ecs
    assert 'command     = ["python", "-m", "alembic", "upgrade", "head"]' in ecs


def test_deploy_workflow_uses_oidc_sha_images_and_migration_first() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "deploy-aws.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(workflow)

    assert parsed is not None
    assert "id-token: write" in workflow
    assert "configure-aws-credentials@v4" in workflow
    assert "aws-access-key-id" not in workflow
    assert "aws-secret-access-key" not in workflow
    assert ":latest" not in workflow
    assert workflow.index("Run one-off Alembic migration") < workflow.index(
        "Deploy services and wait for stability"
    )
    assert "Restore previous task definitions after rollout failure" in workflow
