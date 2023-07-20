"""SQLAlchemy models for item_warehouse."""

from datetime import datetime
from json import dumps
from logging import getLogger
from typing import ClassVar, cast

from _exceptions import DuplicateFieldError, WarehouseNotFoundError
from database import Base
from pydantic import Field, create_model
from schemas import (
    DefaultFunctionType,
    ItemAttributeType,
    ItemBase,
    ItemFieldDefinition,
    ItemUpdateBase,
)
from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.exc import OperationalError
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

    @property
    def item_model(self) -> DeclarativeMeta:
        """Get the SQLAlchemy model for this warehouse's items."""

        if self.name not in self._ITEM_MODELS:
            LOGGER.info("Creating SQLAlchemy model for warehouse %r", self.name)

            model_fields: dict[str, Column[ItemAttributeType] | str] = {
                "created_at": Column(
                    name="created_at",
                    type_=DateTime,  # type: ignore[arg-type]
                    nullable=False,
                    default=datetime.utcnow,
                ),
            }

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
                    if "primary_key_field" in model_fields:
                        raise ValueError(  # noqa: TRY003
                            f"Multiple primary keys defined for warehouse {self.name}"
                        )

                    LOGGER.info(
                        "User-defined primary key %r found in warehouse %r",
                        field_name,
                        self.name,
                    )
                    model_fields["primary_key_field"] = field_name

            if "primary_key_field" not in model_fields:
                model_fields["id"] = Column(
                    "id",
                    Integer,  # type: ignore[arg-type]
                    primary_key=True,
                    index=True,
                )
                model_fields["primary_key_field"] = "id"

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
                field_kwargs: dict[str, object | DefaultFunctionType[object]] = {}

                if callable(field_definition.default):
                    field_kwargs["default_factory"] = field_definition.default
                else:
                    field_kwargs["default"] = field_definition.default

                if max_length := field_definition.type_kwargs.get("length"):
                    field_kwargs["max_length"] = max_length

                pydantic_schema[field_name] = (
                    field_definition.type().python_type,
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
    def pk(self) -> InstrumentedAttribute:
        """Get primary key field for this warehouse."""

        return cast(InstrumentedAttribute, getattr(self.item_model, self.pk_name))

    @property
    def pk_name(self) -> str:
        """Get the name of the primary key field for this warehouse."""

        return cast(str, self.item_model.primary_key_field)
