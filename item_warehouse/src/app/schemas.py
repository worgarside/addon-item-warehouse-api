"""The schemas - valid data shapes - for the item_warehouse app."""

from datetime import datetime
from enum import Enum
from re import Pattern
from re import compile as re_compile
from typing import Any, ClassVar, Generic, Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql.schema import NULL_UNSPECIFIED  # type: ignore[attr-defined]

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

    integer: ItemAttributeType = Integer
    string: ItemAttributeType = String
    text: ItemAttributeType = Text
    datetime: ItemAttributeType = DateTime
    date: ItemAttributeType = Date
    boolean: ItemAttributeType = Boolean
    json: ItemAttributeType = JSON
    float: ItemAttributeType = Float  # noqa: A003


ITEM_TYPE_TYPES = tuple(item_type.value for item_type in ItemType)

# Warehouse Schemas

T = TypeVar("T", bound=ItemAttributeType)


class ItemFieldDefinition(BaseModel, Generic[T]):
    """A Item schema definition."""

    autoincrement: bool | Literal["auto", "ignore_fk"] = "auto"
    default: Any = None
    index: bool | None = None
    key: str | None = None
    nullable: bool | Literal[  # type: ignore[valid-type]
        NULL_UNSPECIFIED
    ] = NULL_UNSPECIFIED
    primary_key: bool = False
    type: T  # noqa: A003
    unique: bool | None = None

    model_config: ClassVar[ConfigDict] = {
        "extra": "forbid",
    }

    @field_validator("type", mode="before")
    def validate_type(
        cls,  # noqa: N805
        typ: ItemAttributeType | str,
    ) -> ItemAttributeType:
        """Validate the ItemFieldDefinition type."""

        if isinstance(typ, str):
            try:
                return ItemType[typ.lower()].value
            except KeyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"type '{typ}' must be a string matching one"
                    f" of `{'`, `'.join(ItemType.__members__.keys())}`.",
                ) from exc

        if typ not in ITEM_TYPE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"type '{typ}' must be a string matching one"
                f" of `{'`, `'.join(ItemType.__members__.keys())}`.",
            )

        return typ

    def model_dump_column(self, field_name: str | None = None) -> Column[T]:
        """Dump the ItemFieldDefinition as a SQLAlchemy Column."""

        params = self.model_dump(exclude_unset=True)

        if field_name is not None:
            params["name"] = field_name

        params["type_"] = params.pop("type")

        return Column(**params)


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    NAME_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^[a-zA-Z0-9_]+$")

    name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    item_schema: dict[str, ItemFieldDefinition[ItemAttributeType]]

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

    @field_serializer("item_schema")
    def serialize_item_schema(
        self, item_schema: dict[str, ItemFieldDefinition[ItemAttributeType]]
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
            raise ValueError("Warehouse name 'warehouse' is reserved.")  # noqa: TRY003

        return name


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
                        },
                        "employee_number": {
                            "unique": True,
                            "nullable": False,
                            "type": "integer",
                            "primary_key": True,
                        },
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


class ItemBase(BaseModel):
    """Base model for items."""

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid",
    }


# Mapping of warehouse name to item schema.
WAREHOUSE_SCHEMAS: dict[str, ItemBase] = {}
