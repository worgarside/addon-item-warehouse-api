"""Custom exceptions for the application."""


from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from json import dumps
from logging import getLogger
from os import environ

from fastapi import HTTPException, status
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)


class _HTTPExceptionBase(ABC, HTTPException):
    """Raised when there is an exception thrown relating to an HTTP request."""

    def __init__(self, *_: object, **__: object) -> None:
        """Initialize the exception."""


def _http_exception_factory(
    name: str, /, response_status: int, detail_template: str | Callable[..., object]
) -> type[_HTTPExceptionBase]:
    """Create an HTTP exception class.

    Args:
        name (str): The name of the exception.
        response_status (int): The HTTP status code to return.
        detail_template (str | Callable[..., object]): The detail message to return.

    Returns:
        type[_HTTPExceptionBase]: The HTTP exception class.
    """

    class _HTTPException(_HTTPExceptionBase):
        """Raised when the user submits a bad request."""

        detail: object  # type: ignore[assignment]

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the exception."""

            if callable(detail_template):
                self.detail = {"type": name, "error": detail_template(*args, **kwargs)}
            else:
                self.detail = {
                    "type": name,
                    "error": detail_template.format(*args, **kwargs),
                }

            self.status_code = response_status

            LOGGER.debug(dumps(self.detail, default=str))

    return _HTTPException


DuplicateFieldError = _http_exception_factory(
    "DuplicateFieldError", status.HTTP_400_BAD_REQUEST, "Field {!r} is duplicated."
)

ItemExistsError = _http_exception_factory(
    "ItemExistsError",
    status.HTTP_400_BAD_REQUEST,
    "Item with PK {!r} already exists in warehouse {!r}",
)

ItemNotFoundError = _http_exception_factory(
    "ItemNotFoundError",
    status.HTTP_404_NOT_FOUND,
    # pylint: disable=consider-using-f-string
    lambda *args, field_name="PK": "Item with {field_name!s} {!r} not found in warehouse {!r}".format(  # noqa: E501
        *args, field_name=field_name
    ),
)

ItemSchemaNotFoundError = _http_exception_factory(
    "ItemSchemaNotFoundError", status.HTTP_404_NOT_FOUND, "Item schema {!r} not found."
)
ItemSchemaExistsError = _http_exception_factory(
    "ItemSchemaExistsError",
    status.HTTP_400_BAD_REQUEST,
    "Item schema {!r} already exists.",
)

InvalidFieldsError = _http_exception_factory(
    "InvalidFieldsError", status.HTTP_400_BAD_REQUEST, "Invalid field(s): {!r}."
)

MissingTypeArgumentError = _http_exception_factory(
    "MissingTypeArgumentError",
    status.HTTP_400_BAD_REQUEST,
    lambda *args: {
        "message": f"Column type {args[0]!s} requires kwarg(s): {args[1]!r}. This may"
        f" be due to the database driver value: {environ['DATABASE_DRIVER_NAME']}",
        "field_config": args[2],
    },
)

TooManyResultsError = _http_exception_factory(
    "TooManyResultsError",
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    "Too many results returned from database query: 1 expected, {} found",
)

UniqueConstraintError = _http_exception_factory(
    "UniqueConstraintError",
    status.HTTP_400_BAD_REQUEST,
    "Field {!r} with value {!r} violates unique constraint.",
)

ValueMustBeOneOfError = _http_exception_factory(
    "ValueMustBeOneOfError",
    status.HTTP_400_BAD_REQUEST,
    lambda value, *enum: f"Value for field {value!r} must be one of:"
    f" {', '.join(str(e) for e in enum)}.",
)

WarehouseExistsError = _http_exception_factory(
    "WarehouseExistsError",
    status.HTTP_400_BAD_REQUEST,
    lambda wh: f"Warehouse {wh.name!r} already exists. Created at {wh.created_at!s}.",
)

WarehouseNotFoundError = _http_exception_factory(
    "WarehouseNotFoundError", status.HTTP_404_NOT_FOUND, "Warehouse {!r} not found."
)
