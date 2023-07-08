"""Endpoint for updating a warehouse in a warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.put("/v1/warehouses/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
) -> dict[str, str]:
    """Update a warehouse in a warehouse."""
    _ = warehouse_id
    return {"message": "warehouse has been created!"}
