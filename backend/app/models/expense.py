"""Authoritative expense business record."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Expense(Base):
    __tablename__ = "expense"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    employee_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    thread_id: Mapped[str] = mapped_column(String, unique=True)
    request_id: Mapped[str] = mapped_column(String)
    expense_type: Mapped[str | None] = mapped_column(String)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    travel_type: Mapped[str | None] = mapped_column(String)
    purpose: Mapped[str | None] = mapped_column(String)
    receipt_available: Mapped[bool | None] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    assessment: Mapped["Assessment | None"] = relationship(back_populates="expense", uselist=False)


class ExpenseIdempotency(Base):
    __tablename__ = "expense_idempotency"
    __table_args__ = {"schema": "app"}

    idempotency_key: Mapped[str] = mapped_column(String, primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    expense_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app.expense.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
