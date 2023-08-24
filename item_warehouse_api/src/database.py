"""Database constants and classes."""

from __future__ import annotations

from datetime import date, datetime
from json import dumps
from logging import getLogger
from os import getenv
from typing import Any, ClassVar, Literal, overload

from schemas import ITEM_TYPE_TYPES, DefaultFunction, GeneralItemModelType
from sqlalchemy import Table
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore[attr-defined]
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


@overload
def _getenv(env_var_name: str, /, default: str, *, no_exist_ok: bool = ...) -> str:
    ...


@overload
def _getenv(
    env_var_name: str, /, default: None = ..., *, no_exist_ok: Literal[True] = True
) -> str:
    ...


@overload
def _getenv(
    env_var_name: str, /, default: None = ..., *, no_exist_ok: Literal[False] = False
) -> str | None:
    ...


def _getenv(
    env_var_name: str, /, default: str | None = None, *, no_exist_ok: bool = False
) -> str | None:
    """Get an environment variable with bashio compatibility.

    Args:
        env_var_name (str): The name of the environment variable to get.
        default (str | None, optional): The default value to return if the environment
            variable is not set. Defaults to None.
        no_exist_ok (bool, optional): Whether to raise an error if the environment
            variable is not set. Defaults to False.

    Raises:
        RuntimeError: If the environment variable is not set and `no_exist_ok` is
            False.

    Returns:
        str | None: The value of the environment variable, the default value, or None.
    """
    env_var = getenv(env_var_name, default)

    # Bashio compatibility (I think)
    if env_var == "null":
        env_var = default

    if env_var or no_exist_ok:
        LOGGER.debug("Environment variable %r is set to %r", env_var_name, env_var)
        return env_var

    raise RuntimeError(f"Missing environment variable: {env_var_name}")  # noqa: TRY003


if _DATABASE_URL := _getenv("DATABASE_URL", no_exist_ok=True):
    LOGGER.info("Using DATABASE_URL environment variable.")
    SQLALCHEMY_DATABASE_URL = _DATABASE_URL
else:
    try:
        DATABASE_USERNAME = _getenv("DATABASE_USERNAME")
        DATABASE_PASSWORD = _getenv("DATABASE_PASSWORD")
        DATABASE_DRIVER_NAME = _getenv("DATABASE_DRIVER_NAME")
        DATABASE_HOST = _getenv("DATABASE_HOST", "homeassistant.local")
        DATABASE_PORT = int(_getenv("DATABASE_PORT", "3306"))
        DATABASE_NAME = _getenv("DATABASE_NAME", "item_warehouse")

        LOGGER.info("Using environment variables for database connection.")
        SQLALCHEMY_DATABASE_URL = f"{DATABASE_DRIVER_NAME}://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"  # noqa: E501
    except KeyError as exc:
        raise RuntimeError(  # noqa: TRY003
            f"Missing environment variable: {exc!s}"
        ) from exc


class _BaseExtra:
    """Extra functionality for SQLAlchemy models."""

    __table__: Table

    ENGINE: ClassVar[Engine]

    def __init__(self, *_: Any, **__: Any) -> None:
        raise NotImplementedError(
            "Class _BaseExtra should not be instantiated by itself or as the primary"
            " base class for a model. Use `Base` instead."
        )

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

    def as_dict(
        self, include: list[str] | None = None, exclude: list[str] | None = None
    ) -> GeneralItemModelType:
        """Convert a SQLAlchemy model to a dict.

        Args:
            self (DeclarativeMeta): The SQLAlchemy model to convert.
            include (list[str] | None, optional): The fields to include. Defaults to
                None (all).
            exclude (list[str] | None, optional): The fields to exclude. Defaults to
                None.

        Raises:
            TypeError: If this instance is not a SQLAlchemy model.

        Returns:
            GeneralItemModelType: The converted model.
        """
        include = sorted(include or self.__table__.columns.keys())
        exclude = exclude or []

        if not isinstance(self, Base):
            raise TypeError(  # noqa: TRY003
                f"Expected a SQLAlchemy model, got {self.__class__!r}."
            )

        fields: GeneralItemModelType = {}

        for field in include:
            if field in exclude:
                continue

            fields[field] = self._serialize(getattr(self, field))

        return fields


_BaseExtra.ENGINE = create_engine(
    SQLALCHEMY_DATABASE_URL,
    json_serializer=_BaseExtra._custom_json_serializer,  # pylint: disable=protected-access
    connect_args={"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {},
)

Base = declarative_base(cls=_BaseExtra)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_BaseExtra.ENGINE)

__all__ = ["Base", "SessionLocal", "GeneralItemModelType"]
