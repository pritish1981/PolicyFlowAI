"""Authoritative exception request separate from checkpoint state."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.review import Review


class ExceptionRequest(Base):
    __tablename__ = "exception_request"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    expense_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app.expense.id"), unique=True)
    assessment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app.assessment.id"), unique=True)
    thread_id: Mapped[str] = mapped_column(String, unique=True)
    justification: Mapped[str] = mapped_column(Text)
    information_history: Mapped[list] = mapped_column(JSONB, default=list)
    variance_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String)
    summary_status: Mapped[str] = mapped_column(String, default="PENDING")
    summary_json: Mapped[dict | None] = mapped_column(JSONB)
    resume_status: Mapped[str] = mapped_column(String, default="NOT_REQUIRED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reviews: Mapped[list["Review"]] = relationship(back_populates="exception", order_by="Review.reviewed_at")
