"""Database constants and classes."""

from datetime import date, datetime
from json import dumps
from logging import getLogger
from typing import Any

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.orm.decl_api import DeclarativeMeta
from wg_utilities.loggers import add_stream_handler

from item_warehouse.src.app.schemas import ITEM_TYPE_TYPES, ItemFieldDefinition

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)

# DATABASE_USERNAME = environ["DATABASE_USERNAME"]  # noqa: ERA001
# DATABASE_PASSWORD = environ["DATABASE_PASSWORD"]  # noqa: ERA001
# DATABASE_HOST = getenv("DATABASE_HOST", "homeassistant.local")  # noqa: ERA001
# DATABASE_PORT = int(getenv("DATABASE_PORT", "3306"))  # noqa: ERA001
# DATABASE_NAME = getenv("DATABASE_NAME", "item_warehouse")  # noqa: ERA001

# SQLALCHEMY_DATABASE_URL = f"mariadb+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"  # noqa: E501 ERA001
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"


def _custom_json_serializer(*args: Any, **kwargs: Any) -> str:
    def _serialize(obj: Any) -> Any:
        if obj in ITEM_TYPE_TYPES:
            return obj.__name__.lower()

        if isinstance(obj, ItemFieldDefinition):
            return 1 / 0

        return obj

    return dumps(*args, default=_serialize, **kwargs)


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    json_serializer=_custom_json_serializer,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()


def as_dict(self: DeclarativeMeta) -> dict[str, object | None]:
    """Convert a SQLAlchemy model to a dict.

    Args:
        self (DeclarativeMeta): The SQLAlchemy model to convert.

    Returns:
        dict[str, object | None]: The converted model.
    """

    fields: dict[str, object | None] = {}

    for field in dir(self):
        if field.startswith("_") or field in ("as_dict", "metadata", "registry"):
            continue

        data = getattr(self, field)

        if isinstance(data, (date | datetime)):
            LOGGER.debug("Dumping %r from model %r", data, self)
            fields[field] = data.isoformat()
        else:
            try:
                dumps(data)
            except TypeError:
                LOGGER.error(
                    "Unable to dump %s in field %s for model %r", data, field, self
                )
                fields[field] = None
            else:
                LOGGER.debug("Dumping %r from model %r", data, self)
                fields[field] = data

    return fields


Base.as_dict = as_dict
