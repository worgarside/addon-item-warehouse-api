"""The schemas - valid data shapes - for the item_warehouse app."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from enum import Enum
from json import dumps
from logging import getLogger
from os import getenv
from re import Pattern
from re import compile as re_compile
from typing import Annotated, ClassVar, Generic, Literal, TypeVar
from uuid import uuid4

from annotated_types import Len
from bidict import MutableBidict, bidict
from exceptions import MissingTypeArgumentError, ValueMustBeOneOfError
from fastapi import HTTPException, status
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    FieldValidationInfo,
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

STRING_REQUIRES_LENGTH = (
    getenv("DATABASE_DRIVER_NAME", "+pymysql").split("+")[-1] == "pymysql"
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

SQL_NAME_PATTERN = re_compile(r"^[a-zA-Z0-9_]+$")


def _validate_sql_identifier(value: str) -> str:
    """Validate a SQL identifier.

    Args:
        value (str): The value to validate.

    Raises:
        ValueError: If the value is not a valid SQL identifier.

    Returns:
        str: The value, if it is a valid SQL identifier.
    """
    if not SQL_NAME_PATTERN.fullmatch(value):
        raise ValueError(f"{value!r} is not a valid SQL identifier.")  # noqa: TRY003

    return value


SqlStr = Annotated[
    str,
    Len(min_length=1, max_length=64),
    AfterValidator(_validate_sql_identifier),
]

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
            "client_ip": lambda: None,  # Always overridden in ItemBase.model_validate
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

    _STRING_PATTERN: ClassVar[Pattern[str]] = re_compile(r"^string\((\d+)\)$")

    autoincrement: bool | Literal["auto", "ignore_fk"] = "auto"
    default: object | DefaultFunction[T] = None
    index: bool | None = None
    key: SqlStr | None = None
    nullable: bool | Literal[  # type: ignore[valid-type]
        NULL_UNSPECIFIED
    ] = NULL_UNSPECIFIED
    primary_key: bool = False
    type_kwargs: dict[SqlStr, object] = Field(default_factory=dict)
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
    def json_serialize_type(self, typ: T) -> str:
        """Serialize the Item type."""

        return typ.__name__.lower()

    @field_validator("type", mode="before")
    def validate_type(cls, typ: str | T, info: FieldValidationInfo) -> T:  # noqa: N805
        """Validate the ItemFieldDefinition type field."""

        if isinstance(typ, str):
            try:
                LOGGER.debug("Converting string %r to ItemType", typ)
                typ = ItemType[typ.lower()].value  # type: ignore[assignment]
            except KeyError as exc:
                raise ValueMustBeOneOfError(
                    typ, ItemType.__members__.keys(), cls._STRING_PATTERN.pattern
                ) from exc

        if isinstance(typ, type):
            # Not isinstance because typ is a literal type
            if typ not in ITEM_TYPE_TYPES:
                raise ValueMustBeOneOfError(
                    typ, ItemType.__members__.keys(), cls._STRING_PATTERN.pattern
                )

            if (
                typ == String
                and STRING_REQUIRES_LENGTH
                and "length" not in info.data.get("type_kwargs", ())
            ):
                raise MissingTypeArgumentError(
                    String, "length", info.data | {"type": repr(typ)}
                )

        return typ  # type: ignore[return-value]

    @field_validator("default", mode="before")
    def validate_default(
        cls, default: object | DefaultFunction[T]  # noqa: N805
    ) -> object | DefaultFunction[T]:
        """Validate the ItemFieldDefinition default field."""

        if isinstance(default, str):
            match default.split(":", 1):
                case "func", func_name:
                    default_func: DefaultFunction[T] | None
                    if not (default_func := DefaultFunction.get_by_name(func_name)):
                        raise ValueMustBeOneOfError(
                            func_name,
                            DefaultFunction.get_names(),
                        )

                    default = default_func
                case _:
                    pass

        return default

    def model_dump_column(self, field_name: str | None = None) -> Column[T]:
        """Dump the ItemFieldDefinition as a SQLAlchemy Column."""

        params = self.model_dump(exclude_unset=True)

        if field_name is not None:
            params["name"] = field_name

        type_ = params.pop("type")

        if type_kwargs := params.pop("type_kwargs", None):
            type_ = type_(**type_kwargs)

        params["type_"] = type_

        LOGGER.debug(
            "Dumping ItemFieldDefinition as Column: %s",
            dumps(params, indent=2, sort_keys=True, default=repr),
        )

        return Column(**params)


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    name: SqlStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_name: SqlStr
    item_schema: dict[
        SqlStr,
        ItemFieldDefinition[ItemAttributeType],
    ]

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
                            "type_kwargs": {"length": 255},
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
                            "type_kwargs": {"length": 64},
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

    @model_validator(mode="before")
    def validate_model(
        cls, values: dict[str, object]  # noqa: N805
    ) -> dict[str, object]:
        """Validate the Item model."""

        client_ip = values.pop("_request.client.host", None)

        for field, v in cls.model_fields.items():
            if (
                not values.get(field)
                and isinstance(v.default_factory, DefaultFunction)
                and v.default_factory.ref == "func:client_ip"
            ):
                LOGGER.debug("Found client_ip field: %s", field)
                if not client_ip:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Missing client IP for field {field!r}.",
                    )

                values[field] = client_ip

        return values


class ItemResponse(ItemBase):
    """Base model for items."""

    model_config: ClassVar[ConfigDict] = {
        "arbitrary_types_allowed": True,
        "extra": "allow",
    }


class ItemUpdateBase(BaseModel):
    """Base model for item update requests."""

    model_config: ClassVar[ConfigDict] = {
        "extra": "allow",
    }


ItemSchema = dict[SqlStr, ItemFieldDefinition[ItemAttributeType]]

GeneralItemModelType = dict[SqlStr, object | None]
