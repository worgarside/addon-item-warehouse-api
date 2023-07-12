"""SQLAlchemy models for item_warehouse."""

from logging import getLogger

from sqlalchemy import JSON, Column, DateTime, Integer, String

from item_warehouse.src.app.schemas import ItemType
from datetime import datetime
from .database import Base, engine

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")

# Mapping of warhouse name to models
WAREHOUSE_MODELS: dict[str, Base] = {}


class Warehouse(Base):  # type: ignore[misc]
    """A Warehouse is just a table: a place where items are stored."""

    __tablename__ = "warehouse"

    name = Column("name", String(255), primary_key=True, unique=True, index=True)
    item_name = Column("item_name", String(255),  unique=True, nullable=False)
    item_schema = Column("item_schema", JSON, nullable=False)
    created_at = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)

    def create_warehouse(self) -> None:
        """Create a new physical table for storing items in."""

        self.item_model.__table__.create(bind=engine)

        WAREHOUSE_MODELS[self.name] = self.item_model


    @property
    def item_model(self) -> Base:
        """Get the SQLAlchemy model for this warehouse's items."""

        if self.name in WAREHOUSE_MODELS:
            return WAREHOUSE_MODELS[self.name]

        model_fields = {
            "id": Column(Integer, primary_key=True, index=True),
            "created_at": Column(DateTime, nullable=False, default=datetime.utcnow),
        }

        for field_name, schema in self.item_schema.items():
            if field_name in model_fields:
                raise ValueError(
                    f"Duplicate column {field_name!r} found, unable to create table."
                )

            model_fields[field_name] = Column(ItemType[schema["type"]].value, nullable=schema["nullable"])

        model_fields["__tablename__"] = self.name

        item_name_camel_case = "".join(
            word.capitalize() for word in self.item_name.split("_")
        )

        return type(item_name_camel_case, (Base,), model_fields)

