"""SQLAlchemy models for item_warehouse."""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String

from .database import Base, engine


class Warehouse(Base):  # type: ignore[misc]
    """A record of all warehouses that have been created.

    A Warehouse is just a table: a place where items are stored.
    """

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    item_name = Column(String(255), nullable=False)
    item_attributes = Column(JSON, nullable=False)
    created_at = Column(DateTime)

    def create_item_table(self) -> None:
        """Create a table for storing items in this warehouse."""

        Item = type(
            self.item_name,
            (Base,),
            {
                "__tablename__": self.item_name,
                "id": Column(Integer, primary_key=True, index=True),
                "created_at": Column(DateTime),
            },
        )

        Base.metadata.create_all(bind=engine)


class ExampleItem(Base):  # type: ignore[misc]
    """Example item for testing."""

    __tablename__ = "example_warehouse"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    name = Column(String(255), unique=True, index=True)
    age = Column(Integer)
    height = Column(Integer)
    weight = Column(Integer)
    alive = Column(Boolean)
