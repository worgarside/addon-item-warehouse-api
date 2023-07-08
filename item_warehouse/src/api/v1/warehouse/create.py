"""Endpoint for creating a warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.post("/v1/warehouses")
def create_warehouse() -> dict[str, str]:
    """Create a warehouse."""
    return {"message": "warehouse has been created!"}
