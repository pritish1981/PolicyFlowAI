"""Ingest the six synthetic policy documents from the project root."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.cache.redis_client import redis_client
from app.db.session import SessionLocal
from app.rag.ingestion.loader import ingest_directory


def main() -> None:
    for result in ingest_directory(ROOT / "policies" / "synthetic", SessionLocal, redis_client):
        print(result)


if __name__ == "__main__":
    main()
