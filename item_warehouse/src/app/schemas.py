"""The schemas - valid data shapes - for the item_warehouse app."""

from datetime import datetime

from pydantic import BaseModel, Field


class WarehouseBase(BaseModel):
    """A simple Warehouse schema."""

    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WarehouseCreate(WarehouseBase):
    """The request schema for creating a warehouse."""


class Warehouse(WarehouseBase):
    """Warehouse ORM schema."""

    id: int

    class Config:
        """Pydantic config."""

        from_attributes = True
