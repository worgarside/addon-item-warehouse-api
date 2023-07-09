"""CRUD operations for the warehouse app."""

from sqlalchemy.orm import Session

from item_warehouse.src.app.models import Warehouse as WarehouseModel
from item_warehouse.src.app.schemas import WarehouseCreate


def create_warehouse(db: Session, warehouse: WarehouseCreate) -> WarehouseModel:
    """Create a warehouse."""
    db_warehouse = WarehouseModel(name=warehouse.name, created_at=warehouse.created_at)
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse


def delete_warehouse(db: Session, warehouse_id: int) -> None:
    """Delete a warehouse."""
    db.query(WarehouseModel).filter(WarehouseModel.id == warehouse_id).delete()
    db.commit()


def get_warehouse(db: Session, warehouse_id: int) -> WarehouseModel | None:
    """Get a warehouse."""
    return db.query(WarehouseModel).filter(WarehouseModel.id == warehouse_id).first()


def get_warehouses(
    db: Session, offset: int = 0, limit: int = 100
) -> list[WarehouseModel]:
    """Get a list of warehouses."""
    return db.query(WarehouseModel).offset(offset).limit(limit).all()


def get_warehouse_by_name(db: Session, name: str) -> WarehouseModel | None:
    """Get a warehouse by its name."""
    return db.query(WarehouseModel).filter(WarehouseModel.name == name).first()
