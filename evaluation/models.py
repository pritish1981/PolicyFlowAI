"""Versioned, strict golden-dataset contracts and loaders."""
from decimal import Decimal
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyGoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(min_length=1)
    question: str = Field(min_length=3)
    expected_policy_code: str | None
    expected_section_id: str | None = None
    expected_relevant_ids: list[str] = Field(default_factory=list)
    required_fact: str | None
    category: str | None = None
    region: str | None = None
    travel_type: str | None = None
    expected_evidence_status: Literal["GROUNDED", "INSUFFICIENT_INFORMATION"] = "GROUNDED"

    @model_validator(mode="after")
    def relevance_is_explicit(self) -> "PolicyGoldenCase":
        if self.expected_policy_code and not self.expected_relevant_ids:
            self.expected_relevant_ids = [self.expected_policy_code]
        if self.expected_evidence_status == "GROUNDED" and not self.expected_relevant_ids:
            raise ValueError(f"case {self.id}: grounded case requires relevance judgments")
        if self.expected_evidence_status == "INSUFFICIENT_INFORMATION" and self.expected_policy_code:
            raise ValueError(f"case {self.id}: unsupported case cannot expect a policy")
        return self


class ExpenseGoldenCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(min_length=1)
    expense_type: Literal["HOTEL", "MEAL", "TAXI"]
    travel_type: Literal["DOMESTIC", "INTERNATIONAL"]
    amount: Decimal = Field(gt=0)
    receipt_available: bool
    expected_decision: Literal[
        "COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"]
    expected_limit: Decimal | None
    expected_sources: list[str]
    as_of: str | None = None

    @model_validator(mode="after")
    def decision_has_expected_limit(self) -> "ExpenseGoldenCase":
        if self.expected_decision == "INSUFFICIENT_INFORMATION":
            if self.expected_limit is not None:
                raise ValueError(f"case {self.id}: insufficient case cannot have a limit")
        elif self.expected_limit is None:
            raise ValueError(f"case {self.id}: decided case requires an exact limit")
        return self


def load_policy_cases(path: str | Path) -> list[PolicyGoldenCase]:
    return _load(path, PolicyGoldenCase)


def load_expense_cases(path: str | Path) -> list[ExpenseGoldenCase]:
    return _load(path, ExpenseGoldenCase)


def _load(path: str | Path, schema):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path}: dataset root must be a list")
    cases = []
    for index, item in enumerate(raw):
        try:
            cases.append(schema.model_validate(item))
        except Exception as error:
            case_id = item.get("id", f"index-{index}") if isinstance(item, dict) else f"index-{index}"
            raise ValueError(f"{path}: invalid case {case_id}: {error}") from error
    identifiers = [case.id for case in cases]
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate case IDs: {', '.join(duplicates)}")
    return cases
