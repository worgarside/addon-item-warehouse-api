"""Endpoint for updating an item in a warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.put("/v1/items/{item_id}")
def update_item(
    item_id: int,
) -> dict[str, str]:
    """Update an item in a warehouse."""
    _ = item_id
    return {"message": "Item has been created!"}
