"""Endpoint for deleting a warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.delete("/v1/warehouses/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
) -> dict[str, str]:
    """Delete a warehouse."""
    _ = warehouse_id
    return {"message": "warehouse has been deleted!"}
