"""Strict contracts for human-owned expense exception review."""
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.policy import PolicyCitation


class ExceptionStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_MORE_INFORMATION = "REQUEST_MORE_INFORMATION"


class _TextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ExceptionCreate(_TextRequest):
    justification: str = Field(min_length=20, max_length=4000)


class ExceptionInformation(_TextRequest):
    information: str = Field(min_length=10, max_length=4000)


class ReviewAction(_TextRequest):
    decision: ReviewDecision
    comments: str = Field(min_length=3, max_length=2000)


class ReviewResumePayload(ReviewAction):
    exception_id: UUID
    reviewer_id: str = Field(min_length=1, max_length=200)


class ExceptionReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=2000)
    key_facts: list[str] = Field(default_factory=list, max_length=20)
    risk_or_attention_points: list[str] = Field(default_factory=list, max_length=20)
    citation_chunk_ids: list[UUID] = Field(default_factory=list)


class ExceptionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exception_id: UUID
    expense_id: UUID
    thread_id: str
    status: ExceptionStatus
    variance_amount: Decimal | None = None
    next_action: Literal["WAIT_FOR_REVIEW", "PROVIDE_MORE_INFORMATION", "COMPLETE"]
    reviewer_comments: str | None = None


class ReviewListItem(BaseModel):
    exception_id: UUID
    expense_id: UUID
    expense_type: str
    amount: Decimal
    currency: str
    policy_limit: Decimal | None
    variance_amount: Decimal | None
    justification: str
    created_at: str


class ReviewDetail(ReviewListItem):
    thread_id: str
    status: ExceptionStatus
    purpose: str
    location: str
    summary_status: Literal["AVAILABLE", "UNAVAILABLE", "PENDING"]
    review_summary: ExceptionReviewSummary | None = None
    citations: list[PolicyCitation] = Field(default_factory=list)
    information_history: list[str] = Field(default_factory=list)
    latest_reviewer_comments: str | None = None
