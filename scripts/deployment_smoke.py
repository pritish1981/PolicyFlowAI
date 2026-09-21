"""Validate a deployed PolicyFlow frontend, backend, readiness, and pgvector."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    request = Request(url, headers={"User-Agent": "policyflow-deployment-smoke/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"body": body}
        return exc.code, payload


def fetch_text(url: str, timeout: float) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "policyflow-deployment-smoke/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.status, response.read(512).decode("utf-8", errors="replace")


def check_pgvector(database_url: str) -> str:
    import psycopg

    psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(psycopg_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            row = cursor.fetchone()
    if row is None:
        raise RuntimeError("pgvector extension is not installed")
    return str(row[0])


def run(base_url: str, timeout: float, database_url: str | None = None) -> dict[str, Any]:
    base = base_url.rstrip("/")
    frontend_status, _ = fetch_text(f"{base}/", timeout)
    health_status, health = fetch_json(f"{base}/health", timeout)
    ready_status, readiness = fetch_json(f"{base}/ready", timeout)

    if frontend_status != 200:
        raise RuntimeError(f"frontend returned HTTP {frontend_status}")
    if health_status != 200 or health.get("status") != "ok":
        raise RuntimeError(f"backend health failed: HTTP {health_status} {health}")
    if ready_status != 200 or readiness.get("status") != "ready":
        raise RuntimeError(f"backend readiness failed: HTTP {ready_status} {readiness}")

    result: dict[str, Any] = {
        "status": "passed",
        "frontend": frontend_status,
        "health": health_status,
        "readiness": ready_status,
    }
    if database_url:
        result["pgvector_version"] = check_pgvector(database_url)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--database-url")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.base_url, args.timeout, args.database_url), indent=2))
        return 0
    except (RuntimeError, URLError, TimeoutError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
