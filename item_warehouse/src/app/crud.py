"""CRUD operations for the warehouse app."""

from dataclasses import field
from datetime import datetime
from pydantic import BaseModel, create_model
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logging import getLogger
from item_warehouse.src.app.models import Warehouse as WarehouseModel, WAREHOUSE_MODELS
from item_warehouse.src.app.schemas import ItemType, WarehouseCreate, WAREHOUSE_SCHEMAS, ItemFieldDefinition
from wg_utilities.loggers import add_stream_handler
from item_warehouse.src.app._dependencies import get_db
from wg_utilities.exceptions import on_exception


# Warehouse Operations


LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)

def _create_pydantic_schema(item_name:str, item_schema: dict[str, ItemFieldDefinition]) -> BaseModel:
    """Create a Pydantic schema from the SQLAlchemy model."""
    
    # If this is called with the result from `get_item_schemas` then the field
    # definitions need to be instatiated as `ItemFieldDefinition` objects.
    if any(isinstance(field_definition, dict) for field_definition in item_schema.values()):
        item_schema_parsed = {
            field_name: ItemFieldDefinition(**field_definition) for field_name, field_definition in item_schema.items()
        }
    else:
        item_schema_parsed = item_schema

    pydantic_schema = {
        "created_at": (datetime, ...),
    }

    for field_name, field_definition in item_schema_parsed.items():
        pydantic_schema[field_name] = (field_definition.type().python_type, field_definition.default)

    item_name_camel_case = "".join(
        word.capitalize() for word in item_name.split("_")
    )

    schema = create_model(item_name_camel_case, **pydantic_schema)

    schema.__fields__["created_at"].default_factory = datetime.utcnow

    return schema

def create_warehouse(db: Session, warehouse: WarehouseCreate) -> WarehouseModel:
    """Create a warehouse."""
    db_warehouse = WarehouseModel(**warehouse.model_dump(exclude_unset=True, mode="json"))

    db_warehouse.create_warehouse()

    item_schema = _create_pydantic_schema(warehouse.item_name, warehouse.item_schema)

    LOGGER.info("Created item schema %r with item name %r", item_schema, warehouse.item_name)

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
    db: Session, offset: int = 0, limit: int = 100
) -> list[WarehouseModel]:
    """Get a list of warehouses."""
    return db.query(WarehouseModel).offset(offset).limit(limit).all()


# Item Schema Operations


def get_item_model(db: Session, item_name: str) -> dict[str, str] | None:
    """Get an item's schema."""
    return (
        db.query(WarehouseModel.item_schema)
        .filter(WarehouseModel.item_name == item_name)
        .first()
    )


def get_item_schemas(db: Session) -> dict[str, dict[str, str]]:
    """Get a list of items and their schemas."""
    return dict(db.query(WarehouseModel.item_name, WarehouseModel.item_schema))

# @on_exception(lambda _: None, raise_after_callback=False, default_return_value=[])
def get_warehouse_item_schemas(db: Session) -> dict[str, dict[str, str]]:
    """Get a list of warehouses and their items' schemas."""
    return db.query(WarehouseModel.name,WarehouseModel.item_name, WarehouseModel.item_schema)


# Item Operations

def create_item(db: Session, warehouse_name: str, item: dict[str, str]) -> dict[str, str]:
    """Create an item in a warehouse"""

    warehouse = get_warehouse(db, warehouse_name)

    if warehouse is None:
        raise ValueError(f"Warehouse {warehouse_name!r} does not exist.")

    LOGGER.info("Instantiating item schema from warehouse item_name %r", warehouse.item_name)
    LOGGER.debug("WAREHOUSE_SCHEMAS: %r", WAREHOUSE_SCHEMAS)

    item_schema: BaseModel = WAREHOUSE_SCHEMAS[warehouse_name].parse_obj(item)

    item_model = WAREHOUSE_MODELS[warehouse_name]

    db_item = item_model(**item_schema.model_dump(mode="json"))

    print("*"*100)
    print(db_item)
    print("*"*100)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def _populate_warehouse_schema_lookup():

    try:
        WAREHOUSE_SCHEMAS.update(
            {
                warehouse_name: _create_pydantic_schema(item_name, item_schema) for warehouse_name, item_name,  item_schema in get_warehouse_item_schemas(next(get_db("`WAREHOUSE_SCHEMAS` population")))
            }
        )
    except OperationalError:
        LOGGER.warning("Unable to populate WAREHOUSE_SCHEMAS, database not yet initialized.")
    else:
        LOGGER.debug("WAREHOUSE_SCHEMAS: %r", WAREHOUSE_SCHEMAS)

def _populate_warehouse_model_lookup():
    try:
        for warehouse in get_warehouses(next(get_db("`WAREHOUSE_MODELS` population"))):
            WAREHOUSE_MODELS[warehouse.name] = warehouse.item_model
    except OperationalError:
        LOGGER.warning("Unable to populate WAREHOUSE_MODELS, database not yet initialized.")
    else:
        LOGGER.debug("WAREHOUSE_MODELS: %r", WAREHOUSE_MODELS)


_populate_warehouse_schema_lookup()
_populate_warehouse_model_lookup()
