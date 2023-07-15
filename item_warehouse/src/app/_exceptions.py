"""Custom exceptions for the application."""


class DuplicateColumnError(ValueError):
    """Raised when a column is duplicated."""

    def __init__(self, column_name: str) -> None:
        """Initialize the exception."""
        super().__init__(
            f"Duplicate column {column_name!r} found, unable to create table."
        )


class WarehouseNotFoundError(Exception):
    """Raised when a warehouse is not found."""

    def __init__(self, warehouse_name: str) -> None:
        """Initialize the exception."""
        super().__init__(f"Warehouse {warehouse_name!r} not found.")
