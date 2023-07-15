"""CRUD operations for the warehouse app."""

from logging import getLogger
from typing import TYPE_CHECKING

from fastapi import HTTPException
from pydantic import ValidationError, create_model
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from wg_utilities.loggers import add_stream_handler

from item_warehouse.src.app._dependencies import get_db
from item_warehouse.src.app.models import Warehouse as WarehouseModel
from item_warehouse.src.app.schemas import (
    WAREHOUSE_SCHEMAS,
    ItemAttributeType,
    ItemBase,
    ItemFieldDefinition,
    WarehouseCreate,
)

from ._exceptions import WarehouseNotFoundError

if TYPE_CHECKING:
    from pydantic.main import IncEx
else:
    IncEx = set[str]


LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


# Warehouse Operations


def _create_pydantic_item_base_schema(
    item_name: str,
    item_schema: dict[str, ItemFieldDefinition[ItemAttributeType]] | dict[str, str],
) -> ItemBase:
    """Create a Pydantic schema from the SQLAlchemy model."""

    # If this is called with the result from `get_item_schemas` then the field
    # definitions need to be instatiated as `ItemFieldDefinition` objects.
    item_schema_parsed: dict[str, ItemFieldDefinition[ItemAttributeType]] = {
        field_name: (
            field_definition
            if isinstance(field_definition, ItemFieldDefinition)
            else ItemFieldDefinition.model_validate(field_definition)
        )
        for field_name, field_definition in item_schema.items()
    }

    pydantic_schema = {}

    for field_name, field_definition in item_schema_parsed.items():
        pydantic_schema[field_name] = (
            field_definition.type().python_type,
            field_definition.default,
        )

    item_name_camel_case = "".join(word.capitalize() for word in item_name.split("_"))

    schema: ItemBase = create_model(  # type: ignore[call-overload]
        __model_name=item_name_camel_case,
        __base__=ItemBase,
        **pydantic_schema,
    )

    LOGGER.info("Created Pydantic schema %r: %s", schema, schema.model_json_schema())

    return schema


def create_warehouse(db: Session, warehouse: WarehouseCreate) -> WarehouseModel:
    """Create a warehouse."""
    db_warehouse = WarehouseModel(
        **warehouse.model_dump(exclude_unset=True, by_alias=True)
    )

    db_warehouse.create_warehouse()
    item_schema = _create_pydantic_item_base_schema(
        warehouse.item_name, warehouse.item_schema
    )

    LOGGER.info(
        "Created item schema %r with item name %r", item_schema, warehouse.item_name
    )

    WAREHOUSE_SCHEMAS[warehouse.name] = item_schema

    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse


def delete_warehouse(db: Session, warehouse_name: int) -> None:
    """Delete a warehouse."""
    db.query(WarehouseModel).filter(WarehouseModel.id == warehouse_name).delete()
    db.commit()


def get_warehouse(db: Session, name: str) -> WarehouseModel | None:
    """Get a warehouse by its name."""
    return db.query(WarehouseModel).filter(WarehouseModel.name == name).first()


def get_warehouses(
    db: Session,
    offset: int = 0,
    limit: int = 100,
    *,
    allow_no_warehouse_table: bool = False,
) -> list[WarehouseModel]:
    """Get a list of warehouses.

    Args:
        db (Session): The database session to use.
        offset (int, optional): The offset to use when querying the database.
            Defaults to 0.
        limit (int, optional): The limit to use when querying the database.
            Defaults to 100.
        allow_no_warehouse_table (bool, optional): Whether to suppress the error
            thrown because there is no `warehouse` table. Defaults to False.

    Returns:
        list[WarehouseModel]: A list of warehouses.
    """

    try:
        return db.query(WarehouseModel).offset(offset).limit(limit).all()
    except OperationalError as exc:
        if (
            allow_no_warehouse_table
            and f"no such table: {WarehouseModel.__tablename__}" in str(exc)
        ):
            return []

        raise


# Item Schema Operations


def get_item_model(db: Session, item_name: str) -> dict[str, str] | None:
    """Get an item's schema."""

    if (
        results := db.query(WarehouseModel.item_schema)
        .filter(WarehouseModel.item_name == item_name)
        .first()
    ) is None:
        return None

    return results[0]  # type: ignore[return-value]


def get_item_schemas(db: Session) -> dict[str, dict[str, str]]:
    """Get a list of items and their schemas."""
    return dict(db.query(WarehouseModel.item_name, WarehouseModel.item_schema))


def get_warehouse_item_schemas(
    db: Session, *, allow_no_warehouse_table: bool = False
) -> list[tuple[str, str, dict[str, str]]]:
    """Get a list of warehouses and their items' schemas.

    Args:
        db (Session): The database session to use.
        allow_no_warehouse_table (bool, optional): Whether to suppress the error
            thrown because there is no `warehouse` table. Defaults to False.

    Returns:
        list[tuple[str, str, dict[str, str]]]: A list of tuples containing the warehouse
            name, item name, and item schema.
    """

    try:
        return db.query(
            WarehouseModel.name, WarehouseModel.item_name, WarehouseModel.item_schema
        ).all()
    except OperationalError as exc:
        if (
            allow_no_warehouse_table
            and f"no such table: {WarehouseModel.__tablename__}" in str(exc)
        ):
            return []

        raise


# Item Operations


def create_item(db: Session, warehouse_name: str, item: dict[str, object]) -> ItemBase:
    """Create an item in a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    if warehouse is None:
        raise WarehouseNotFoundError(warehouse_name)

    LOGGER.info(
        "Instantiating item schema from warehouse item_name %r", warehouse.item_name
    )
    LOGGER.debug("WAREHOUSE_SCHEMAS: %r", WAREHOUSE_SCHEMAS)

    try:
        item_schema: ItemBase = WAREHOUSE_SCHEMAS[warehouse_name].model_validate(item)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=[
                {
                    "msg": err["msg"],
                    "loc": err["loc"],
                    "type": err["type"],
                }
                for err in exc.errors()
            ],
        ) from exc

    db_item = warehouse.item_model(**item_schema.model_dump())

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Re-parse so that we've got any new/updated values from the database.
    return WAREHOUSE_SCHEMAS[warehouse_name].model_validate(db_item.as_dict())


def _populate_warehouse_lookups() -> None:
    """Populate the warehouse lookups from pre-existing values in the database."""
    WAREHOUSE_SCHEMAS.update(
        {
            warehouse_name: _create_pydantic_item_base_schema(item_name, item_schema)
            for warehouse_name, item_name, item_schema in get_warehouse_item_schemas(
                next(get_db("`WAREHOUSE_SCHEMAS` population")),
                allow_no_warehouse_table=True,
            )
        }
    )

    LOGGER.debug("WAREHOUSE_SCHEMAS: %r", WAREHOUSE_SCHEMAS)

    for warehouse in get_warehouses(
        next(get_db("`Warehouse._ITEM_MODELS` population")),
        allow_no_warehouse_table=True,
    ):
        # Just accessing the item_model property will create the SQLAlchemy model.
        _ = warehouse.item_model

    LOGGER.debug(
        "Warehouse._ITEM_MODELS: %r",
        WarehouseModel._ITEM_MODELS,  # pylint: disable=protected-access
    )


_populate_warehouse_lookups()
