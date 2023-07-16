"""The schemas - valid data shapes - for the item_warehouse app."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from enum import Enum
from json import dumps
from logging import getLogger
from re import Pattern
from re import compile as re_compile
from typing import Any, ClassVar, Generic, Literal, TypeVar
from uuid import uuid4

from bidict import MutableBidict, bidict
from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
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
from sqlalchemy.types import UserDefinedType
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


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

DFT = TypeVar("DFT", bound=object)

DefaultFunctionType = Callable[..., DFT]


class DefaultFunction(UserDefinedType[DFT]):
    """A default function for an ItemFieldDefinition."""

    _FUNCTIONS: MutableBidict[str, DefaultFunctionType[object]] = bidict(
        {
            "utcnow": datetime.utcnow,
            "today": date.today,
            "uuid4": lambda: str(uuid4()),
        }
    )

    def __init__(self, name: str, func: DefaultFunctionType[object]) -> None:
        """Initialise a default function.

        The class lookup `_FUNCTIONS` is updated with the function if it is not already
        present.
        """
        self.name = name

        if name not in self._FUNCTIONS:
            self._FUNCTIONS[name] = func

        self.func: DefaultFunctionType[object] = self._FUNCTIONS[name]

    def __call__(self) -> object:
        """Call the default function."""
        return self.func()

    def __repr__(self) -> str:
        """Return a representation of the default function."""
        return f"<{self.__class__.__name__} func:{self.name}>"

    def __str__(self) -> str:
        """Return a string representation of the default function."""
        return self.ref

    @property
    def python_type(self) -> type[DFT]:
        """The Python type of the default function.

        Not yet implemented.

        Could be done by inspecting the function signature? Or just calling it and
        checking the type of the return value...
        """
        return NotImplemented

    @property
    def ref(self) -> str:
        """The reference to this default function."""
        return f"func:{self.name}"

    @classmethod
    def get_by_name(cls, name: str) -> DefaultFunction[DFT] | None:
        """Get a default function by its name."""

        if not (func := cls._FUNCTIONS.get(name)):
            return None

        return cls(name, func)

    @classmethod
    def get_names(cls) -> list[str]:
        """Get the names of all the default functions."""

        return sorted(cls._FUNCTIONS.keys())


class ItemFieldDefinition(BaseModel, Generic[T]):
    """A Item schema definition."""

    autoincrement: bool | Literal["auto", "ignore_fk"] = "auto"
    default: object | DefaultFunction[T] = None
    index: bool | None = None
    key: str | None = None
    nullable: bool | Literal[  # type: ignore[valid-type]
        NULL_UNSPECIFIED
    ] = NULL_UNSPECIFIED
    primary_key: bool = False
    type: T  # noqa: A003
    unique: bool | None = None

    model_config: ClassVar[ConfigDict] = {
        "arbitrary_types_allowed": True,
        "extra": "forbid",
    }

    @field_serializer("default", return_type=object, when_used="json")
    def json_serialize_default(self, default: object | DefaultFunction[T]) -> object:
        """Serialize the Item default."""

        if isinstance(default, DefaultFunction):
            return default.ref

        return default

    @field_serializer("type", return_type=str, when_used="json")
    def serialize_type(self, typ: T) -> str:
        """Serialize the Item type."""

        return typ.__name__.lower()

    @model_validator(mode="before")
    def _validate_model(cls, data: dict[str, Any]) -> dict[str, Any]:  # noqa: N805
        """Validate the ItemFieldDefinition model."""

        if isinstance(typ := data["type"], str):
            try:
                LOGGER.debug("Converting string %r to ItemType", typ)
                data["type"] = ItemType[typ.lower()].value
            except KeyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"type {typ!r} must be a string matching one"
                    f" of `{'`, `'.join(ItemType.__members__.keys())}`.",
                ) from exc

        if data["type"] not in ITEM_TYPE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"type {typ!r} must be a string matching one"
                f" of `{'`, `'.join(ItemType.__members__.keys())}`.",
            )

        if (default := data.get("default")) is not None and isinstance(default, str):
            match default.split(":", 1):
                case "func", func_name:
                    try:
                        data["default"] = DefaultFunction.get_by_name(func_name)
                    except KeyError as exc:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"default function {func_name!r} must be one"
                            f" of `{'`, `'.join(DefaultFunction.get_names())}`.",
                        ) from exc
                case _:
                    pass

        LOGGER.debug("Validated ItemFieldDefinition: %r", data)

        return data

    def model_dump_column(self, field_name: str | None = None) -> Column[T]:
        """Dump the ItemFieldDefinition as a SQLAlchemy Column."""

        params = self.model_dump(exclude_unset=True)

        if field_name is not None:
            params["name"] = field_name

        params["type_"] = params.pop("type")

        LOGGER.debug(
            "Dumping ItemFieldDefinition as Column: %s",
            dumps(params, sort_keys=True, default=repr),
        )

        return Column(**params)


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    NAME_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^[a-zA-Z0-9_]+$")

    name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: str = Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=64)
    item_schema: dict[str, ItemFieldDefinition[ItemAttributeType]]

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

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
                            "default": -1,
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
                            "default": "func:utcnow",
                        },
                        "password": {
                            "nullable": False,
                            "type": "string",
                            "default": "func:uuid4",
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

    model_config: ClassVar[ConfigDict] = {
        "arbitrary_types_allowed": True,
        "extra": "forbid",
    }


class ItemResponse(ItemBase):
    """Base model for items."""

    model_config: ClassVar[ConfigDict] = {
        "arbitrary_types_allowed": True,
        "extra": "allow",
    }


ItemSchema = dict[str, ItemFieldDefinition[ItemAttributeType]]
