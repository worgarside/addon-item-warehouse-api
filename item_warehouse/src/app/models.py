"""SQLAlchemy models for item_warehouse."""

from sqlalchemy import Column, DateTime, Integer, String

from .database import Base


class Warehouse(Base):  # type: ignore[misc]
    """A warehouse - a table with a fancy name.

    The `warehouses` table is a record of all warehouses that have been created.
    """

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime)
