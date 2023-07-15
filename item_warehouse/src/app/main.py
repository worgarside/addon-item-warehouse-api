"""API for managing warehouses and items."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum, auto
from json import dumps
from logging import getLogger
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException, Response, status
from fastapi.params import Query
from sqlalchemy.orm import Session
from wg_utilities.loggers import add_stream_handler

from item_warehouse.src.app import crud
from item_warehouse.src.app._dependencies import get_db
from item_warehouse.src.app.database import Base, SessionLocal, engine
from item_warehouse.src.app.models import Warehouse as WarehouseModel
from item_warehouse.src.app.schemas import (
    ItemResponse,
    ItemSchema,
    Warehouse,
    WarehouseCreate,
)

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Populate the item model/schema lookups before the application lifecycle starts."""

    db = SessionLocal()

    try:
        for warehouse in crud.get_warehouses(
            db,
            allow_no_warehouse_table=True,
        ):
            # Just accessing the item_model property will create the SQLAlchemy model.
            __ = warehouse.item_model
            ___ = warehouse.item_schema_class
    finally:
        db.close()

    LOGGER.debug(
        "Warehouse._ITEM_SCHEMAS: %r",
        WarehouseModel._ITEM_SCHEMAS,  # pylint: disable=protected-access
    )
    LOGGER.debug(
        "Warehouse._ITEM_MODELS: %r",
        WarehouseModel._ITEM_MODELS,  # pylint: disable=protected-access
    )

    yield


app = FastAPI(lifespan=lifespan)


class ApiTag(StrEnum):
    """API tags."""

    ITEM = auto()
    ITEM_SCHEMA = auto()
    WAREHOUSE = auto()


# Warehouse Endpoints


@app.post("/v1/warehouses", response_model=Warehouse, tags=[ApiTag.WAREHOUSE])
def create_warehouse(
    warehouse: WarehouseCreate, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Create a warehouse."""

    if warehouse.name == "warehouse":
        raise HTTPException(
            status_code=400,
            detail="Warehouse name 'warehouse' is reserved.",
        )

    if (db_warehouse := crud.get_warehouse(db, warehouse.name)) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Warehouse {warehouse.name!r} already exists. Created"
            f" at {db_warehouse.created_at}",
        )

    if crud.get_item_schema(db, warehouse.item_name) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Item {warehouse.item_name!r} already exists.",
        )

    try:
        return crud.create_warehouse(db, warehouse)
    except Exception as exc:
        LOGGER.exception(repr(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create warehouse {warehouse.name!r}: "{exc}"',
        ) from exc


@app.delete(
    "/v1/warehouses/{warehouse_name}",
    # status_code=status.HTTP_204_NO_CONTENT,   # noqa: ERA001
    response_class=Response,
    tags=[ApiTag.WAREHOUSE],
)
def delete_warehouse(
    warehouse_name: int, db: Session = Depends(get_db)  # noqa: B008
) -> None:
    """Delete a warehouse."""
    crud.delete_warehouse(db, warehouse_name)


@app.get(
    "/v1/warehouses/{warehouse_name}", response_model=Warehouse, tags=[ApiTag.WAREHOUSE]
)
def get_warehouse(
    warehouse_name: str, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Get a warehouse."""

    if (db_warehouse := crud.get_warehouse(db, warehouse_name)) is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    return db_warehouse


@app.get("/v1/warehouses", response_model=list[Warehouse], tags=[ApiTag.WAREHOUSE])
def get_warehouses(
    offset: int = 0, limit: int = 100, db: Session = Depends(get_db)  # noqa: B008
) -> list[WarehouseModel]:
    """List warehouses."""

    return crud.get_warehouses(db, offset=offset, limit=limit)


@app.put("/v1/warehouses/{warehouse_name}", tags=[ApiTag.WAREHOUSE])
def update_warehouse(
    warehouse_name: int,
) -> dict[str, str]:
    """Update a warehouse in a warehouse."""
    _ = warehouse_name
    return {"message": "warehouse has been updated!"}


# Item Schema Endpoints


@app.get(
    "/v1/items/{item_name}/schema/",
    response_model=ItemSchema,
    tags=[ApiTag.ITEM_SCHEMA],
)
def get_item_schema(
    item_name: str, db: Session = Depends(get_db)  # noqa: B008
) -> ItemSchema:
    """Get an item's schema."""
    if (item_model := crud.get_item_schema(db, item_name)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_name!r} not found",
        )

    return item_model


@app.get(
    "/v1/items/schemas",
    response_model=dict[str, ItemSchema],
    tags=[ApiTag.ITEM_SCHEMA],
)
def get_item_schemas(
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, ItemSchema]:
    """Get a list of items' names and schemas."""
    return crud.get_item_schemas(db)


# Item Endpoints


@app.post(
    "/v1/warehouses/{warehouse_name}/items",
    response_model=ItemResponse,
    tags=[ApiTag.ITEM],
)
def create_item(
    warehouse_name: str,
    item: Annotated[
        dict[str, object],
        Body(
            examples=[
                {
                    "name": "Joe Bloggs",
                    "age": 42,
                    "salary": 123456,
                    "alive": True,
                    "hire_date": "2021-01-01",
                    "last_login": "2021-01-01T12:34:56",
                },
            ]
        ),
    ],
    db: Session = Depends(get_db),  # noqa: B008
) -> ItemResponse:
    """Create an item."""

    LOGGER.info("POST\t/v1/warehouses/%s/items", warehouse_name)
    LOGGER.debug(dumps(item))

    return crud.create_item(db, warehouse_name, item)


@app.get(
    "/v1/warehouses/{warehouse_name}/items",
    response_model=list[ItemResponse],
    tags=[ApiTag.ITEM],
)
def get_items(
    warehouse_name: str,
    offset: int = 0,
    limit: int = 100,
    fields: str
    | None = Query(  # type: ignore[assignment] # noqa: B008
        default=None,
        example="age,salary,name,alive",
        description="A comma-separated list of fields to return.",
        pattern=r"^[a-zA-Z0-9_]+(,[a-zA-Z0-9_]+)*$",
    ),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[ItemResponse]:
    """Get items in a warehouse."""

    LOGGER.info("GET\t/v1/warehouses/%s/items", warehouse_name)

    field_names = fields.split(",") if fields else None

    return crud.get_items(
        db, warehouse_name, offset=offset, limit=limit, field_names=field_names
    )


if __name__ == "__main__":
    import uvicorn

    LOGGER.info("Starting server...")
    LOGGER.debug("http://localhost:8000/docs")

    uvicorn.run(app, host="localhost", port=8000)
