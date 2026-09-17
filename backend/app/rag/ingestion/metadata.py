"""Validated metadata for synthetic Markdown policies."""
from datetime import date
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class PolicyMetadata(BaseModel):
    policy_code: str = Field(pattern=r"^POL-[0-9]{3}$")
    title: str
    domain: str = Field(alias="category")
    version: str
    region: str = "GLOBAL"
    travel_type: str = "ALL"
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"
    effective_date: date
    expiry_date: date | None = None

    @field_validator("version", mode="before")
    @classmethod
    def normalize_version(cls, value: object) -> str:
        return str(value)

    @model_validator(mode="after")
    def dates_valid(self) -> "PolicyMetadata":
        if self.expiry_date is not None and self.expiry_date <= self.effective_date:
            raise ValueError("expiry_date must follow effective_date")
        return self


def load_policy(path: Path) -> tuple[PolicyMetadata, str, bytes]:
    """Read frontmatter and Markdown body; retain original bytes for hashing."""
    raw = path.read_bytes()
    source = raw.decode("utf-8")
    parts = source.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"{path}: YAML frontmatter is required")
    metadata = PolicyMetadata.model_validate(yaml.safe_load(parts[1]))
    body = parts[2].strip()
    if not body or "## " not in body:
        raise ValueError(f"{path}: at least one section is required")
    return metadata, body, raw
