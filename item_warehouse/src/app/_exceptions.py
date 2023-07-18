"""Custom exceptions for the application."""


from abc import ABC
from collections.abc import Callable

from fastapi import HTTPException, status


class _HTTPExceptionBase(ABC, HTTPException):
    """Raised when there is an exception thrown relating to an HTTP request."""

    def __init__(self, *_: object, **__: object) -> None:
        """Initialize the exception."""


def _http_exception_factory(
    response_status: int, detail_template: str | Callable[..., object]
) -> type[_HTTPExceptionBase]:
    class _HTTPException(_HTTPExceptionBase):
        """Raised when the user submits a bad request."""

        detail: object  # type: ignore[assignment]

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialize the exception."""

            if callable(detail_template):
                self.detail = detail_template(*args, **kwargs)
            else:
                self.detail = detail_template.format(*args, **kwargs)

            self.status_code = response_status

    return _HTTPException


DuplicateFieldError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST, "Field {!r} is duplicated."
)


HttpValidationError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST,
    lambda exc: [
        {
            "msg": err.get("msg"),
            "loc": err.get("loc"),
            "type": err.get("type"),
        }
        for err in exc.errors()
    ],
)


ItemNotFoundError = _http_exception_factory(
    status.HTTP_404_NOT_FOUND,
    # pylint: disable=consider-using-f-string
    lambda *args, field_name="PK": "Item with {field_name!s} {!r} not found in warehouse {!r}.".format(  # noqa: E501
        *args, field_name=field_name
    ),
)

ItemSchemaNotFoundError = _http_exception_factory(
    status.HTTP_404_NOT_FOUND, "Item schema {!r} not found."
)
ItemSchemaExistsError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST, "Item schema {!r} already exists."
)

InvalidFieldsError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST, "Invalid field(s): {!r}."
)

UniqueConstraintError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST,
    "Field {!r} with value {!r} violates unique constraint.",
)

WarehouseExistsError = _http_exception_factory(
    status.HTTP_400_BAD_REQUEST,
    lambda wh: f"Warehouse {wh.name!r} already exists. Created at {wh.created_at!s}.",
)

WarehouseNotFoundError = _http_exception_factory(
    status.HTTP_404_NOT_FOUND, "Warehouse {!r} not found."
)
