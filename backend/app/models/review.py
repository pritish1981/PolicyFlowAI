"""Immutable human reviewer actions."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.exception_request import ExceptionRequest


class Review(Base):
    __tablename__ = "review"
    __table_args__ = {"schema": "app"}
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    exception_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app.exception_request.id"))
    reviewer_id: Mapped[str] = mapped_column(String(200))
    decision: Mapped[str] = mapped_column(String)
    comments: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    exception: Mapped["ExceptionRequest"] = relationship(back_populates="reviews")
