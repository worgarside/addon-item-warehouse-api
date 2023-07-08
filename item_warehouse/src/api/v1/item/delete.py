"""Endpoint for deleting an item from a warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.delete("/v1/items/{item_id}")
def delete_item(
    item_id: int,
) -> dict[str, str]:
    """Delete an item from a warehouse."""
    _ = item_id
    return {"message": "Item has been deleted!"}
