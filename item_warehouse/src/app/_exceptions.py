"""Custom exceptions for the application."""


from fastapi import HTTPException, status
from pydantic import ValidationError


class DuplicateFieldError(ValueError):
    """Raised when a field is duplicated."""

    def __init__(self, field_name: str) -> None:
        """Initialize the exception."""
        super().__init__(
            f"Duplicate field {field_name!r} found, unable to create table."
        )


class SerializationError(RuntimeError):
    """Raised when a value can't be serialized."""

    def __init__(self, value: object) -> None:
        """Initialize the exception."""
        super().__init__(f"Unable to serialize {value!r}")


class WarehouseNotFoundError(Exception):
    """Raised when a warehouse is not found."""

    def __init__(self, warehouse_name: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Warehouse {warehouse_name!r} not found.")


class HttpValidationError(HTTPException):
    """Raised when a Pydantic validation should be returned as an HTTP error."""

    def __init__(self, validation_error: ValidationError) -> None:
        """Initialize the exception."""

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[
                {
                    "msg": err["msg"],
                    "loc": err["loc"],
                    "type": err["type"],
                }
                for err in validation_error.errors()
            ],
        )
