"""The schemas - valid data shapes - for the item_warehouse app."""

from datetime import datetime
from enum import Enum
from re import Pattern
from re import compile as re_compile
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text

ItemAttributeType = (
    type[Integer]
    | type[String]
    | type[Text]
    | type[DateTime]
    | type[Boolean]
    | type[JSON]
    | type[Float]
)


class ItemType(Enum):
    """The type of an item."""

    integer = Integer
    string = String
    text = Text
    datetime = DateTime
    boolean = Boolean
    json = JSON
    float = Float


ITEM_TYPE_TYPES = tuple(item_type.value for item_type in ItemType)


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    NAME_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^[a-zA-Z0-9_]+$")

    name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    item_attributes: dict[str, ItemAttributeType]

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    @field_serializer("item_attributes")
    def serialize_item_attributes(
        self, item_attributes: dict[str, ItemAttributeType]
    ) -> dict[str, str]:
        """Serialize the Warehouse item_attributes."""

        return {key: value.__name__.lower() for key, value in item_attributes.items()}

    @field_validator("name")
    def validate_name(cls, name: str) -> str:  # noqa: N805
        """Validate the Warehouse name."""
        if name == "warehouses":
            raise ValueError("Warehouse name 'warehouses' is reserved.")

        return name

    @field_validator("item_attributes", mode="before")
    def validate_item_attributes(
        cls, item_attributes: dict[str, Any]  # noqa: N805
    ) -> dict[str, ItemAttributeType]:
        """Validate the Warehouse item_attributes."""

        if not item_attributes:
            raise ValueError("Warehouse item_attributes must not be empty.")

        for key, value in item_attributes.items():
            if not cls.NAME_PATTERN.fullmatch(key):
                raise ValueError(
                    f"item_attributes key '{key}' must match {cls.NAME_PATTERN.pattern!s}."
                )

            if isinstance(value, str) and value.lower() in ItemType.__members__:
                item_attributes[key] = ItemType[value.lower()].value
            elif value not in ITEM_TYPE_TYPES:
                raise ValueError(
                    f"item_attributes value '{value}' must be a string matching one of"
                    f" `{'`, `'.join(ItemType.__members__.keys())}`."
                )

        return item_attributes


class WarehouseCreate(WarehouseBase):
    """The request schema for creating a warehouse."""

    model_config: ClassVar[ConfigDict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "example_warehouse",
                    "item_name": "example_item",
                    "item_attributes": {
                        "name": "string",
                        "age": "integer",
                        "height": "integer",
                        "weight": "integer",
                        "alive": "boolean",
                    },
                }
            ]
        }
    }


class Warehouse(WarehouseBase):
    """Warehouse ORM schema."""

    id: int

    class Config:
        """Pydantic config."""

        from_attributes = True
