"""The base Pydantic model every request/response schema inherits from."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ServiceCatBaseModel(BaseModel):
    """Project-wide Pydantic base: ORM-friendly, strict, whitespace-trimmed."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )
