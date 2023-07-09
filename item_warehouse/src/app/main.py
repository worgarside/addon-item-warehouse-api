"""API for managing warehouses and items."""

from collections.abc import Generator
from logging import StreamHandler, getLogger
from sys import stdout

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from item_warehouse.src.app import crud
from item_warehouse.src.app.database import Base, SessionLocal, engine
from item_warehouse.src.app.models import Warehouse as WarehouseModel
from item_warehouse.src.app.schemas import Warehouse, WarehouseCreate

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
LOGGER.addHandler(StreamHandler(stdout))

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db() -> Generator[Session, None, None]:
    """Get a database connection, and safely close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/v1/warehouses", response_model=Warehouse)
def create_warehouse(
    warehouse: WarehouseCreate, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Create a warehouse."""
    if (db_warehouse := crud.get_warehouse_by_name(db, warehouse.name)) is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Warehouse already exists. Created at {db_warehouse.created_at}",
        )

    if warehouse.name == "warehouses":
        raise HTTPException(
            status_code=400,
            detail=f"Warehouse name '{warehouse.name}' is reserved.",
        )

    return crud.create_warehouse(db, warehouse)


@app.delete(
    "/v1/warehouses/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_warehouse(
    warehouse_id: int, db: Session = Depends(get_db)  # noqa: B008
) -> None:
    """Delete a warehouse."""
    crud.delete_warehouse(db, warehouse_id)


@app.get("/v1/warehouses/{warehouse_id}", response_model=Warehouse)
def get_warehouse(
    warehouse_id: int, db: Session = Depends(get_db)  # noqa: B008
) -> WarehouseModel:
    """Get a warehouse from the warehouse."""

    if (db_warehouse := crud.get_warehouse(db, warehouse_id)) is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    return db_warehouse


@app.get("/v1/warehouses", response_model=list[Warehouse])
def get_warehouses(
    offset: int = 0, limit: int = 100, db: Session = Depends(get_db)  # noqa: B008
) -> list[WarehouseModel]:
    """List warehouses."""

    return crud.get_warehouses(db, offset=offset, limit=limit)


@app.put("/v1/warehouses/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
) -> dict[str, str]:
    """Update a warehouse in a warehouse."""
    _ = warehouse_id
    return {"message": "warehouse has been updated!"}
