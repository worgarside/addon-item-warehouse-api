"""API for managing warehouses and items."""
from __future__ import annotations

try:
    from enum import StrEnum, auto
except ImportError:
    # pylint: disable=ungrouped-imports
    from sys import version

    if not version.startswith("3.10"):
        raise

    # This is just for Pynguin
    from enum import auto  # noqa: I001
    from strenum import StrEnum  # type: ignore[import,no-redef]

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from json import dumps
from logging import getLogger
from typing import Annotated, Any

import crud
from _dependencies import get_db
from database import SQLALCHEMY_DATABASE_URL, Base, SessionLocal
from exceptions import ItemSchemaExistsError, WarehouseExistsError
from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.params import Query
from fastapi.responses import JSONResponse
from models import Warehouse as WarehouseModel
from pydantic import ValidationError
from schemas import (
    GeneralItemModelType,
    ItemResponse,
    ItemSchema,
    SqlStr,
    Warehouse,
    WarehouseCreate,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)

try:
    Base.metadata.create_all(bind=WarehouseModel.ENGINE)
except OperationalError:
    LOGGER.debug(SQLALCHEMY_DATABASE_URL)
    raise


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

    LOGGER.debug(
        "Warehouse._ITEM_SCHEMAS: %r",
        WarehouseModel._ITEM_SCHEMAS,  # pylint: disable=protected-access
    )
    LOGGER.debug(
        "Warehouse._ITEM_MODELS: %r",
        WarehouseModel._ITEM_MODELS,  # pylint: disable=protected-access
    )


app = FastAPI(lifespan=lifespan)


class ApiTag(StrEnum):
    """API tags."""

    ITEM = auto()
    ITEM_SCHEMA = auto()
    WAREHOUSE = auto()


@app.exception_handler(ValidationError)
def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    LOGGER.debug("400 Bad Request")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=[
            {
                "msg": err.get("msg"),
                "loc": err.get("loc"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ],
    )


@app.exception_handler(RequestValidationError)
def request_validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI request validation errors."""
    LOGGER.debug("400 Bad Request")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=[
            {
                "msg": err.get("msg"),
                "loc": err.get("loc"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ],
    )


@app.exception_handler(ResponseValidationError)
def response_validation_error_handler(
    _: Request, exc: ResponseValidationError
) -> JSONResponse:
    """Handle FastAPI response validation errors."""
    LOGGER.debug("500 Internal Server Error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=[
            {
                "msg": err.get("msg"),
                "loc": err.get("loc"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ],
    )


# Warehouse Endpoints


@app.post(
    "/v1/warehouses",
    response_model=Warehouse,
    tags=[ApiTag.WAREHOUSE],
    response_model_exclude_unset=True,
)
def create_warehouse(
    warehouse: WarehouseCreate, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Create a warehouse."""

    if (
        db_warehouse := crud.get_warehouse(db, warehouse.name, no_exist_ok=True)
    ) is not None:
        raise WarehouseExistsError(db_warehouse)

    if crud.get_item_schema(db, warehouse.item_name, no_exist_ok=True) is not None:
        raise ItemSchemaExistsError(warehouse.item_name)

    return crud.create_warehouse(db, warehouse)


@app.delete(
    "/v1/warehouses/{warehouse_name}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[ApiTag.WAREHOUSE],
)
def delete_warehouse(
    warehouse_name: str, db: Session = Depends(get_db)  # noqa: B008
) -> None:
    """Delete a warehouse."""
    crud.delete_warehouse(db, warehouse_name)


@app.get(
    "/v1/warehouses/{warehouse_name}",
    response_model=Warehouse,
    tags=[ApiTag.WAREHOUSE],
    response_model_exclude_unset=True,
)
def get_warehouse(
    warehouse_name: str, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Get a warehouse."""

    return crud.get_warehouse(db, warehouse_name)


@app.get(
    "/v1/warehouses",
    response_model=list[Warehouse],
    tags=[ApiTag.WAREHOUSE],
    response_model_exclude_unset=True,
)
def get_warehouses(
    offset: int = 0, limit: int = 100, db: Session = Depends(get_db)  # noqa: B008
) -> list[WarehouseModel]:
    """List warehouses."""

    return crud.get_warehouses(db, offset=offset, limit=limit)


@app.put("/v1/warehouses/{warehouse_name}", tags=[ApiTag.WAREHOUSE])
def update_warehouse(
    warehouse_name: str,
    warehouse: WarehouseCreate,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, str]:
    """Update a warehouse in a warehouse."""
    return crud.update_warehouse(db, warehouse_name, warehouse)


# Item Schema Endpoints


@app.get(
    "/v1/items/{item_name}/schema/",
    response_model=ItemSchema,
    tags=[ApiTag.ITEM_SCHEMA],
    response_model_exclude_unset=True,
)
def get_item_schema(
    item_name: str, db: Session = Depends(get_db)  # noqa: B008
) -> ItemSchema:
    """Get an item's schema."""
    return crud.get_item_schema(db, item_name)


@app.get(
    "/v1/items/schemas",
    response_model=dict[SqlStr, ItemSchema],
    tags=[ApiTag.ITEM_SCHEMA],
    response_model_exclude_unset=True,
)
def get_item_schemas(
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, ItemSchema]:
    """Get a list of items' names and schemas."""
    return crud.get_item_schemas(db)


# Item Endpoints


@app.post(
    "/v1/warehouses/{warehouse_name}/items",
    response_model=Any,
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
    request: Request,
    db: Session = Depends(get_db),  # noqa: B008
) -> ItemResponse:
    """Create an item."""

    LOGGER.info("POST\t/v1/warehouses/%s/items", warehouse_name)
    LOGGER.debug(dumps(item))

    if client := request.client:
        item.update({"_request.client.host": client.host})

    res = crud.create_item(db, warehouse_name, item)

    LOGGER.info("RESPONSE: %r", res)

    return res


@app.delete(
    "/v1/warehouses/{warehouse_name}/items/{item_pk}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    tags=[ApiTag.ITEM],
)
def delete_item(
    warehouse_name: str,
    item_pk: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete an item in a warehouse."""

    LOGGER.info("DELETE\t/v1/warehouses/%s/items/%s", warehouse_name, item_pk)

    crud.delete_item(db, warehouse_name, item_pk)


@app.get(
    "/v1/warehouses/{warehouse_name}/items/{item_pk}",
    response_model=ItemResponse,
    tags=[ApiTag.ITEM],
)
def get_item(
    warehouse_name: str,
    item_pk: str,
    fields: str
    | None = Query(  # type: ignore[assignment] # noqa: B008
        default=None,
        example="age,salary,name,alive",
        description="A comma-separated list of fields to return.",
        pattern=r"^[a-zA-Z0-9_]+(,[a-zA-Z0-9_]+)*$",
    ),
    db: Session = Depends(get_db),  # noqa: B008
) -> GeneralItemModelType:
    """Get an item in a warehouse."""

    LOGGER.info("GET\t/v1/warehouses/%s/items/%s", warehouse_name, item_pk)

    field_names = fields.split(",") if fields else None

    if not (
        item := crud.get_item(db, warehouse_name, item_pk, field_names=field_names)
    ):
        warehouse = get_warehouse(warehouse_name, db=db)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found. Note: PK field is `{warehouse.item_model.primary_key_field}`",
        )

    return item


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


@app.put(
    "/v1/warehouses/{warehouse_name}/items/{item_pk}",
    response_model=ItemResponse,
    tags=[ApiTag.ITEM],
)
def update_item(
    warehouse_name: str,
    item_pk: str,
    item: Annotated[
        dict[str, object],
        Body(
            examples=[
                {
                    "name": "Joseph Bloggs",
                    "salary": 0,
                    "alive": False,
                },
            ]
        ),
    ],
    db: Session = Depends(get_db),  # noqa: B008
) -> GeneralItemModelType:
    """Update an item in a warehouse."""

    LOGGER.info("PUT\t/v1/warehouses/%s/items/%s", warehouse_name, item_pk)
    LOGGER.debug(dumps(item))

    if not crud.get_item(db, warehouse_name, item_pk):
        warehouse = get_warehouse(warehouse_name, db=db)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found. Note: PK field is `{warehouse.item_model.primary_key_field}`",
        )

    return crud.update_item(
        db, warehouse_name=warehouse_name, item_pk=item_pk, item_update=item
    )


if __name__ == "__main__":
    import uvicorn

    LOGGER.info("Starting server...")
    LOGGER.debug("http://localhost:8002/docs")

    uvicorn.run(app, host="0.0.0.0", port=8002)  # noqa: S104
else:
    LOGGER.debug("http://localhost:8000/docs")
