"""Database constants and classes."""

from datetime import date, datetime
from json import dumps
from logging import getLogger
from typing import Any, ClassVar

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore[attr-defined]
from sqlalchemy.orm.decl_api import DeclarativeMeta
from wg_utilities.loggers import add_stream_handler

from item_warehouse.src.app.schemas import ITEM_TYPE_TYPES, DefaultFunction

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


class BaseExtra:
    """Extra functionality for SQLAlchemy models."""

    ENGINE: ClassVar[Engine]

    def __init__(self, *_: Any, **__: Any) -> None:  # noqa: D107
        raise NotImplementedError(  # noqa: TRY003
            "Class BaseExtra should not be instantiated by itself or as the primary"
            f" base class for a model. Use {Base.__name__} instead."
        )

    def as_dict(self) -> dict[str, object | None]:
        """Convert a SQLAlchemy model to a dict.

        Args:
            self (DeclarativeMeta): The SQLAlchemy model to convert.

        Raises:
            TypeError: If this instance is not a SQLAlchemy model.

        Returns:
            dict[str, object | None]: The converted model.
        """

        if not isinstance(self, Base):
            raise TypeError(  # noqa: TRY003
                f"Expected a SQLAlchemy model, got {self.__class__!r}."
            )

        fields: dict[str, object | None] = {}

        for field in dir(self):
            if field.startswith("_") or field in (
                "as_dict",
                "metadata",
                "registry",
                "ENGINE",
            ):
                continue

            fields[field] = self._serialize(getattr(self, field))

        return fields

    @classmethod
    def _custom_json_serializer(cls, *args: Any, **kwargs: Any) -> str:
        return dumps(*args, default=cls._serialize, **kwargs)

    @classmethod
    def _serialize(cls, obj: Any) -> Any:
        if isinstance(obj, DefaultFunction):
            return obj.ref

        if obj in ITEM_TYPE_TYPES:
            return obj.__name__.lower()

        if isinstance(obj, (date | datetime)):
            return obj.isoformat()

        dumps(obj)

        return obj


BaseExtra.ENGINE = create_engine(
    SQLALCHEMY_DATABASE_URL,
    json_serializer=BaseExtra._custom_json_serializer,  # pylint: disable=protected-access
    connect_args={"check_same_thread": False},
)

Base: DeclarativeMeta = declarative_base()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=BaseExtra.ENGINE)
