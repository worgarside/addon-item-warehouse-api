"""CRUD operations for the warehouse app."""

from logging import getLogger
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from wg_utilities.loggers import add_stream_handler

from item_warehouse.src.app.models import Warehouse as WarehouseModel
from item_warehouse.src.app.schemas import (
    ItemBase,
    ItemResponse,
    ItemSchema,
    WarehouseCreate,
)

from ._exceptions import HttpValidationError, WarehouseNotFoundError

if TYPE_CHECKING:
    from pydantic.main import IncEx
else:
    IncEx = set[str]


LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


# Warehouse Operations


def create_warehouse(db: Session, /, warehouse: WarehouseCreate) -> WarehouseModel:
    """Create a warehouse."""
    db_warehouse = WarehouseModel(
        **warehouse.model_dump(exclude_unset=True, by_alias=True)
    )

    db_warehouse.intialise_warehouse()

    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)

    return db_warehouse


def delete_warehouse(db: Session, /, warehouse_name: int) -> None:
    """Delete a warehouse."""
    db.query(WarehouseModel).filter(WarehouseModel.id == warehouse_name).delete()
    db.commit()


def get_warehouse(db: Session, /, name: str) -> WarehouseModel | None:
    """Get a warehouse by its name."""
    return db.query(WarehouseModel).filter(WarehouseModel.name == name).first()


def get_warehouses(
    db: Session,
    /,
    *,
    offset: int = 0,
    limit: int = 100,
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


def get_item_schema(db: Session, /, item_name: str) -> ItemSchema | None:
    """Get an item's schema."""

    if (
        results := db.query(WarehouseModel.item_schema)
        .filter(WarehouseModel.item_name == item_name)
        .first()
    ) is None:
        return None

    return results[0]  # type: ignore[return-value]


def get_item_schemas(db: Session, /) -> dict[str, ItemSchema]:
    """Get a list of items and their schemas."""
    return dict(db.query(WarehouseModel.item_name, WarehouseModel.item_schema))


# Item Operations


def create_item(
    db: Session, warehouse_name: str, item: dict[str, object]
) -> ItemResponse:
    """Create an item in a warehouse."""

    warehouse = get_warehouse(db, warehouse_name)

    if warehouse is None:
        raise WarehouseNotFoundError(warehouse_name)

    try:
        item_schema: ItemBase = warehouse.item_schema_class.model_validate(item)
    except ValidationError as exc:
        raise HttpValidationError(exc) from exc

    db_item = warehouse.item_model(**item_schema.model_dump())

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Re-parse so that we've got any new/updated values from the database.
    return warehouse.item_schema_class.model_validate(
        db_item.as_dict()
    )  # type: ignore[return-value]


def get_items(
    db: Session,
    /,
    warehouse_name: str,
    field_names: list[str] | None = None,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[ItemResponse]:
    """Get a list of items in a warehouse.

    Args:
        db (Session): The database session to use.
        warehouse_name (str): The name of the warehouse to get the items from.
        field_names (list[str], optional): The names of the fields to return. Defaults
            to None.
        offset (int, optional): The offset to use when querying the database.
            Defaults to 0.
        limit (int, optional): The limit to use when querying the database. Defaults
            to 100.

    Returns:
        list[dict[str, object]]: A list of items in the warehouse.

    Raises:
        WarehouseNotFoundError: Raised if the warehouse does not exist.
    """

    if (warehouse := get_warehouse(db, warehouse_name)) is None:
        raise WarehouseNotFoundError(warehouse_name)

    if not field_names:
        return [  # type: ignore[var-annotated]
            item.as_dict()
            for item in db.query(warehouse.item_model).offset(offset).limit(limit).all()
        ]

    field_names = sorted(field_names)

    try:
        fields = tuple(
            getattr(warehouse.item_model, field_name) for field_name in field_names
        )
    except AttributeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field: {exc}",
        ) from exc

    results = db.query(*fields).offset(offset).limit(limit).all()

    return [dict(zip(field_names, row, strict=True)) for row in results]  # type: ignore[misc]
