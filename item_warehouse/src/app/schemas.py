"""The schemas - valid data shapes - for the item_warehouse app."""

from datetime import datetime
from re import Pattern
from re import compile as re_compile
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class ItemAttributeType

class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    NAME_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^[a-zA-Z0-9_]+$")

    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: str
    item_attributes: dict[str, str]

    @field_validator("name", "item_name")
    def validate_name(cls, name: str) -> str:  # noqa: N805
        """Validate the Warehouse/Item name."""
        if name == "warehouses":
            raise ValueError("Warehouse name 'warehouses' is reserved.")

        if not cls.NAME_PATTERN.fullmatch(name):
            raise ValueError(
                f"Warehouse name '{name}' must match {cls.NAME_PATTERN.pattern!s}."
            )

        return name


class WarehouseCreate(WarehouseBase):
    """The request schema for creating a warehouse."""


class Warehouse(WarehouseBase):
    """Warehouse ORM schema."""

    id: int

    class Config:
        """Pydantic config."""

        from_attributes = True
