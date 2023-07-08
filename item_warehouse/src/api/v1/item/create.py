"""Endpoint for creating an item."""

from fastapi import FastAPI

app = FastAPI()


@app.post("/v1/items")
def create_item() -> dict[str, str]:
    """Create an item."""
    return {"message": "Item has been created!"}
