"""Append-only sanitized business audit event."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = {"schema": "app"}
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String)
    request_id: Mapped[str | None] = mapped_column(String)
    thread_id: Mapped[str | None] = mapped_column(String)
    expense_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    exception_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    review_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    actor_id: Mapped[str | None] = mapped_column(String(200))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
