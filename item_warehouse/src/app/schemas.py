"""The schemas - valid data shapes - for the item_warehouse app."""

from datetime import datetime
from enum import Enum
from operator import index
from re import Pattern
from re import compile as re_compile
from typing import Any, ClassVar
from fastapi import HTTPException, status

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text, null


# Mapping of warehouse name to item schema.
WAREHOUSE_SCHEMAS = {}

ItemAttributeType = (
    type[Integer]
    | type[String]
    | type[Text]
    | type[DateTime]
    | type[Date]
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
    date = Date
    boolean = Boolean
    json = JSON
    float = Float


ITEM_TYPE_TYPES = tuple(item_type.value for item_type in ItemType)

# Warehouse Schemas


class ItemFieldDefinition(BaseModel):
    """A Item schema definition."""

    autoincrement: bool = False
    default: Any = None
    index: bool | None = None
    key: str | None = None
    nullable: bool = True
    primary_key: bool = False
    type: ItemAttributeType
    unique: bool = False

    @field_validator("type", mode="before")
    def validate_type(cls, typ: ItemAttributeType | str) -> ItemAttributeType:
        """Validate the ItemFieldDefinition type."""

        if isinstance(typ, str) and typ.lower() in ItemType.__members__:
            return ItemType[typ.lower()].value

        if typ not in ITEM_TYPE_TYPES:
            raise ValueError(
                f"type '{typ}' must be a string matching one"
                f" of `{'`, `'.join(ItemType.__members__.keys())}`."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"type '{typ}' must be a string matching one"
                f" of `{'`, `'.join(ItemType.__members__.keys())}`."
            )

        return typ


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    NAME_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^[a-zA-Z0-9_]+$")

    name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    item_schema: dict[str, ItemFieldDefinition]

    model_config: ClassVar[ConfigDict] = {
        "arbitrary_types_allowed" : True
    }

    @field_serializer("item_schema")
    def serialize_item_schema(
        self, item_schema: dict[str, ItemFieldDefinition]
    ) -> dict[str, dict[str, bool | str]]:
        """Serialize the Warehouse item_schema."""

        serialized_schema = {}

        for name, definition in item_schema.items():
            serialized_schema[name] = {
                key: value
                for key, value in definition.model_dump(exclude_unset=True).items()
                if key != "type"
            }

            serialized_schema[name]["type"] = definition.type.__name__.lower()

        return serialized_schema

    @field_validator("name")
    def validate_name(cls, name: str) -> str:  # noqa: N805
        """Validate the Warehouse name."""
        if name == "warehouse":
            raise ValueError("Warehouse name 'warehouse' is reserved.")

        return name

    @field_validator("item_schema", mode="before")
    def validate_item_schema(
        cls, item_schema: dict[str, dict[str, object]]  # noqa: N805
    ) -> dict[str, ItemFieldDefinition]:
        """Validate the Warehouse item_schema."""

        if not item_schema:
            raise ValueError("Warehouse item_schema must not be empty.")

        for field_name, schema in item_schema.items():
            if not cls.NAME_PATTERN.fullmatch(field_name):
                raise ValueError(
                    f"item schema field_name '{field_name}' must match"
                    f" {cls.NAME_PATTERN.pattern!s}."
                )

            typ = schema.get("type", None)

            if isinstance(typ, str) and typ.lower() in ItemType.__members__:
                item_schema[field_name]["type"] = ItemType[typ.lower()].value
            elif typ not in ITEM_TYPE_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name!r} type '{typ}' must be a string matching one"
                    f" of `{'`, `'.join(ItemType.__members__.keys())}`."
                )

        return item_schema


class WarehouseCreate(WarehouseBase):
    """The request schema for creating a warehouse."""

    model_config: ClassVar[ConfigDict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "payroll",
                    "item_name": "employee",
                    "item_schema": {
                        "name": {
                            "nullable": False,
                            "type": "string",
                        },
                        "age": {
                            "nullable": True,
                            "type": "integer",
                        },
                        "salary": {
                            "nullable": False,
                            "type": "integer",
                        },
                        "alive": {
                            "nullable": False,
                            "type": "boolean",
                        },
                        "hire_date": {
                            "nullable": False,
                            "type": "date",
                        },
                        "last_login": {
                            "nullable": True,
                            "type": "datetime",
                        }
                    },
                }
            ]
        }
    }


class Warehouse(WarehouseBase):
    """Warehouse ORM schema."""

    model_config: ClassVar[ConfigDict] = {
        "from_attributes": True,
    }


# Item Schemas

ItemBase = dict[
    str,
    bool
    | float
    | int
    | str
    | datetime
    | dict[str, bool | float | int | str | datetime],
]

