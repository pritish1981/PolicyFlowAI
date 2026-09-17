"""Token-protected policy ingestion endpoint."""
import hmac
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.cache.redis_client import redis_client
from app.core.config import settings
from app.db.session import SessionLocal
from app.rag.ingestion.loader import IngestionBusy, ingest_directory

router = APIRouter(prefix="/api/v1/admin/policies", tags=["policy-admin"])
CORPUS = Path(__file__).resolve().parents[4] / "policies" / "synthetic"


class IngestResponse(BaseModel):
    results: list[dict[str, object]]


@router.post("/ingest", response_model=IngestResponse)
def ingest(x_policy_admin_token: str | None = Header(default=None)) -> IngestResponse:
    """Reindex synthetic policy files after token verification."""
    if not settings.policy_admin_token or not x_policy_admin_token or not hmac.compare_digest(x_policy_admin_token, settings.policy_admin_token):
        raise HTTPException(status_code=403, detail="Policy admin token required")
    try:
        return IngestResponse(results=ingest_directory(CORPUS, SessionLocal, redis_client))
    except IngestionBusy as exc:
        raise HTTPException(status_code=409, detail="Policy ingestion already running") from exc
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
