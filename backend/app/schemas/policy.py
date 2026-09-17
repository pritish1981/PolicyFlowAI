"""Policy Q&A HTTP and structured model contracts."""
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SAFE_ABSTENTION = "I could not find enough verified policy evidence to answer this question reliably."


class EvidenceStatus(StrEnum):
    GROUNDED = "GROUNDED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class PolicyQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    region: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("question", "category", "region", mode="before")
    @classmethod
    def trim_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class PolicyCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: UUID
    policy_code: str
    policy_version: str
    section_id: str
    section_title: str
    excerpt: str


class PolicyAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    answer: str
    citations: list[PolicyCitation]
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def grounded_requires_citations(self) -> "PolicyAnswerResponse":
        if self.evidence_status == EvidenceStatus.GROUNDED and not self.citations:
            raise ValueError("grounded answers require verified citations")
        if self.evidence_status == EvidenceStatus.INSUFFICIENT_INFORMATION and self.citations:
            raise ValueError("insufficient-information responses cannot contain citations")
        return self


class GroundedPolicyAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=8000)
    citation_chunk_ids: list[UUID] = Field(default_factory=list)
    insufficient_information: bool = False

    @field_validator("answer", mode="before")
    @classmethod
    def trim_answer(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def citations_match_status(self) -> "GroundedPolicyAnswer":
        if self.insufficient_information and self.citation_chunk_ids:
            raise ValueError("insufficient-information output cannot cite chunks")
        return self
