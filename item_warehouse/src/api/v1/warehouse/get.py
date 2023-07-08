"""Endpoint for getting a warehouse from the warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/v1/warehouses/{warehouse_id}")
def get_warehouse(
    warehouse_id: int,
) -> dict[str, str]:
    """Get a warehouse from the warehouse."""
    _ = warehouse_id
    return {"message": "warehouse has been gotten!"}
