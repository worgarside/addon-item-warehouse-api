"""SQLAlchemy models for item_warehouse."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from json import dumps
from logging import getLogger
from typing import Any, ClassVar, Self

from database import Base
from exceptions import DuplicateFieldError, InvalidFieldsError, WarehouseNotFoundError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FieldValidationInfo,
    create_model,
    field_serializer,
    field_validator,
)
from schemas import (
    DefaultFunctionType,
    GeneralItemModelType,
    ItemAttributeType,
    ItemBase,
    ItemFieldDefinition,
    ItemResponse,
    ItemUpdateBase,
    PythonType,
    QueryParamType,
)
from schemas import Warehouse as WarehouseSchema
from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.exc import OperationalError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.decl_api import DeclarativeMeta
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


class Warehouse(Base):  # type: ignore[misc]
    """A Warehouse is just a table: a place where items are stored."""

    __tablename__ = "warehouse"

    _ITEM_MODELS: ClassVar[dict[str, DeclarativeMeta]] = {}
    _ITEM_SCHEMAS: ClassVar[dict[str, ItemBase]] = {}
    _ITEM_UPDATE_SCHEMAS: ClassVar[dict[str, ItemUpdateBase]] = {}

    name: Column[str] = Column(
        name="name", type_=String(length=255), primary_key=True, unique=True, index=True
    )
    item_name: Column[str] = Column(
        name="item_name", type_=String(length=255), unique=True, nullable=False
    )
    item_schema: Column[dict[str, ItemFieldDefinition[ItemAttributeType]]] = Column(
        name="item_schema", type_=JSON, nullable=False  # type: ignore[arg-type]
    )
    created_at: Column[datetime] = Column(
        name="created_at", type_=DateTime, nullable=False, default=datetime.utcnow
    )

    @classmethod
    def get_item_model_for_warehouse(
        cls, warehouse_name: str
    ) -> DeclarativeMeta | None:
        """Get the SQLAlchemy model for the given warehouse.

        Args:
            warehouse_name (str): The name of the warehouse to get the model for.

        Returns:
            DeclarativeMeta | None: The SQLAlchemy item model for the given warehouse.
        """

        return cls._ITEM_MODELS.get(warehouse_name)

    def search_params_are_pks(self, search_params: dict[str, Any]) -> bool:
        """Check if the given search params are the primary key for this warehouse.

        Args:
            search_params (GeneralItemModelType): The search params to check.

        Returns:
            bool: True if the search params are the primary key for this warehouse,
                False otherwise.
        """
        return sorted(self.pk_name) == sorted(search_params.keys())

    def drop(self, *, no_exist_ok: bool = False) -> None:
        """Drop the physical table for storing items in."""

        LOGGER.info("Dropping warehouse %r", self.name)

        try:
            self.item_model.__table__.drop(bind=self.ENGINE)
        except OperationalError as exc:
            if "unknown table" in str(exc).lower():
                if not no_exist_ok:
                    raise WarehouseNotFoundError(self.name) from exc

                LOGGER.info(
                    "Warehouse %r does not exist, so not dropping it.", self.name
                )
            else:
                raise
        finally:
            Base.metadata.remove(self.item_model.__table__)

            self._ITEM_MODELS.pop(self.name, None)
            self._ITEM_SCHEMAS.pop(self.name, None)

    def intialise_warehouse(self) -> None:
        """Create a new physical table for storing items in."""

        LOGGER.info("Creating warehouse %r", self.name)

        self.item_model.__table__.create(bind=self.ENGINE)

    def parse_pk_dict(
        self, pk_dict: GeneralItemModelType | QueryParamType
    ) -> tuple[PythonType, ...]:
        """Parse a PK dict into a tuple of SQLAlchemy PK objects for comparison.

        Args:
            pk_dict (dict[str, str]): The primary key dict to parse.

        Returns:
            tuple[PythonType, ...]: The parsed primary key objects.
        """

        if not self.search_params_are_pks(pk_dict):
            raise InvalidFieldsError(
                sorted(pk_dict.keys()),
            )

        item_pk = []

        for pk in self.pk:
            if pk.type.python_type in (date, datetime):
                item_pk.append(pk.type.python_type.fromisoformat(pk_dict[pk.name]))
            else:
                item_pk.append(pk.type.python_type(pk_dict[pk.name]))

        return tuple(item_pk)

    @property
    def item_model(self) -> DeclarativeMeta:
        """Get the SQLAlchemy model for this warehouse's items."""

        if self.name not in self._ITEM_MODELS:
            LOGGER.info("Creating SQLAlchemy model for warehouse %r", self.name)

            model_fields: dict[str, Column[ItemAttributeType] | str] = {}

            user_defined_pk = False

            _field_def: ItemFieldDefinition[ItemAttributeType]
            for field_name, _field_def in self.item_schema.items():
                if field_name in model_fields:
                    raise DuplicateFieldError(field_name)

                field_definition: ItemFieldDefinition[
                    ItemAttributeType
                ] = ItemFieldDefinition.model_validate(_field_def)

                model_fields[field_name] = field_definition.model_dump_column(
                    field_name=field_name
                )

                if field_definition.primary_key:
                    user_defined_pk = True
                    LOGGER.info(
                        "User-defined primary key %r found in warehouse %r",
                        field_name,
                        self.name,
                    )

            if not user_defined_pk:
                model_fields["id"] = Column(
                    "id",
                    Integer,  # type: ignore[arg-type]
                    primary_key=True,
                    index=True,
                )

            model_fields["__tablename__"] = self.name

            LOGGER.debug(
                "Model fields:\n%s",
                dumps(model_fields, indent=2, default=repr, sort_keys=True),
            )

            item_name_camel_case = "".join(
                word.capitalize() for word in self.item_name.split("_")
            )

            self._ITEM_MODELS[self.name] = type(  # type: ignore[assignment]
                item_name_camel_case, (Base,), model_fields
            )

        return self._ITEM_MODELS[self.name]

    @property
    def item_schema_class(self) -> ItemBase:
        """Create a Pydantic schema from the SQLAlchemy model."""

        if self.name not in self._ITEM_SCHEMAS:
            item_schema_parsed: dict[str, ItemFieldDefinition[ItemAttributeType]]

            item_schema_parsed = {
                field_name: ItemFieldDefinition.model_validate(field_definition)
                for (
                    field_name,
                    field_definition,
                ) in self.item_schema.items()
            }

            pydantic_schema = {}

            for field_name, field_definition in item_schema_parsed.items():
                field_kwargs: dict[
                    str, PythonType | DefaultFunctionType[PythonType]
                ] = {}

                if callable(field_definition.default):
                    field_kwargs["default_factory"] = field_definition.default
                else:
                    field_kwargs["default"] = field_definition.default

                if max_length := field_definition.type_kwargs.get("length"):
                    field_kwargs["max_length"] = max_length

                field_type = (
                    field_definition.type().python_type | None
                    if field_definition.nullable is True
                    else field_definition.type().python_type
                )

                pydantic_schema[field_name] = (
                    field_type,
                    Field(**field_kwargs),  # type: ignore[arg-type,pydantic-field]
                )

            item_name_camel_case = "".join(
                word.capitalize() for word in self.item_name.split("_")
            )

            schema: ItemBase = create_model(  # type: ignore[call-overload]
                __model_name=item_name_camel_case,
                __base__=ItemBase,
                **pydantic_schema,
            )

            LOGGER.info(
                "Created Pydantic schema %r: %s", schema, schema.model_json_schema()
            )

            self._ITEM_SCHEMAS[self.name] = schema

        return self._ITEM_SCHEMAS[self.name]

    @property
    def pk(self) -> tuple[InstrumentedAttribute, ...]:
        """Get primary key field(s) for this warehouse."""

        return tuple(
            getattr(self.item_model, pk.name)
            for pk in inspect(self.item_model).primary_key
        )

    @property
    def pk_name(self) -> tuple[str, ...]:
        """Get the name of the primary key field(s) for this warehouse."""

        return tuple(pk.name for pk in inspect(self.item_model).primary_key)


class _Page(BaseModel):
    """A paginated response."""

    count: int
    max_page: int
    page: int
    total: int

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

    @classmethod
    def empty(cls) -> Self:
        """Create an empty page."""

        raise NotImplementedError


class ItemPage(_Page):
    """A paginated response of items."""

    items: Sequence[GeneralItemModelType] | Sequence[ItemResponse]

    include_fields: bool = Field(default=False, exclude=True)
    fields: list[str] = Field(default_factory=list, validate_default=True)

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

    @field_validator("fields", mode="before")
    def validate_fields(
        cls, _: list[str] | None, info: FieldValidationInfo  # noqa: N805
    ) -> list[str] | None:
        """Ensure fields is populated if include_fields is True."""

        if info.data["include_fields"] and (items := info.data["items"]):
            return list(items[0].keys())

        return []

    @classmethod
    def empty(cls) -> ItemPage:
        """Create an empty page."""

        return cls(count=0, total=0, max_page=0, page=0, items=[])


class SchemaPage(_Page):
    """A paginated response of schemas."""

    schemas: list[WarehouseSchema]

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

    @classmethod
    def empty(cls) -> SchemaPage:
        """Create an empty page."""

        return cls(count=0, total=0, max_page=0, page=0, schemas=[])


class WarehousePage(_Page):
    """A paginated response of warehouses."""

    warehouses: list[Warehouse]

    model_config: ClassVar[ConfigDict] = {"arbitrary_types_allowed": True}

    @classmethod
    def empty(cls) -> WarehousePage:
        """Create an empty page."""

        return cls(count=0, total=0, max_page=0, page=0, warehouses=[])

    @field_serializer("warehouses", when_used="json")
    def serialize_warehouses(
        self, warehouses: list[Warehouse]
    ) -> list[WarehouseSchema]:
        """Serialize warehouses to schemas."""

        return [WarehouseSchema.model_validate(warehouse) for warehouse in warehouses]
