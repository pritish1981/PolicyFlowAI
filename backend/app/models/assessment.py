"""Persisted deterministic assessment separate from graph state."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    expense_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app.expense.id"), unique=True)
    decision: Mapped[str] = mapped_column(String)
    policy_rule_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    citations_json: Mapped[list] = mapped_column(JSONB, default=list)
    policy_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    explanation: Mapped[str] = mapped_column(Text)
    next_action: Mapped[str] = mapped_column(String)
    model_name: Mapped[str | None] = mapped_column(String)
    prompt_version: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expense: Mapped["Expense"] = relationship(back_populates="assessment")
