"""Phase 004 expense intake, rule extraction, and assessment contracts."""
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.policy import PolicyCitation


class ExpenseType(StrEnum):
    HOTEL = "HOTEL"
    MEAL = "MEAL"
    TAXI = "TAXI"


class TravelType(StrEnum):
    DOMESTIC = "DOMESTIC"
    INTERNATIONAL = "INTERNATIONAL"


class Decision(StrEnum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class ExpenseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expense_type: ExpenseType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: Literal["INR"] | None = None
    location: str | None = Field(default=None, min_length=1, max_length=200)
    travel_type: TravelType | None = None
    purpose: str | None = Field(default=None, min_length=1, max_length=1000)
    receipt_available: bool | None = None

    @field_validator("location", "purpose", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    def missing_fields(self) -> list[str]:
        return [name for name in type(self).model_fields if getattr(self, name) is None]


class ExpenseClarification(ExpenseCreate):
    @model_validator(mode="after")
    def nonempty_update(self) -> "ExpenseClarification":
        if not self.model_fields_set:
            raise ValueError("at least one clarification field is required")
        return self


class RuleType(StrEnum):
    AMOUNT_LIMIT = "AMOUNT_LIMIT"
    RECEIPT_REQUIRED = "RECEIPT_REQUIRED"
    PROHIBITION = "PROHIBITION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_type: RuleType
    category: str
    amount_limit: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: Literal["INR"] | None = None
    travel_type: TravelType | None = None
    unit: Literal["PER_NIGHT", "PER_DAY", "PER_TRIP", "PER_TRANSACTION"] | None = None
    condition: str | None = None
    source_chunk_ids: list[UUID] = Field(min_length=1)

    @model_validator(mode="after")
    def numeric_rule_has_threshold(self) -> "PolicyRule":
        if self.rule_type in (RuleType.AMOUNT_LIMIT, RuleType.RECEIPT_REQUIRED):
            if self.amount_limit is None or self.currency != "INR":
                raise ValueError("numeric rule requires an INR threshold")
        return self


class PolicyRuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rules: list[PolicyRule] = Field(default_factory=list)
    insufficient_information: bool = False


class ExpenseAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expense_id: UUID
    thread_id: str
    request_id: str
    decision: Decision
    policy_limit: Decimal | None = None
    confidence: Decimal = Field(ge=0, le=1)
    explanation: str
    citations: list[PolicyCitation] = Field(default_factory=list)
    next_action: Literal["NONE", "PROVIDE_CLARIFICATION", "SUBMIT_EXCEPTION_JUSTIFICATION", "RETRY_LATER"] = "NONE"
    missing_fields: list[str] = Field(default_factory=list)
