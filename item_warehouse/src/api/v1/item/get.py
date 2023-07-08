"""Endpoint for getting an item from the warehouse."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/v1/items/{item_id}")
def get_item(
    item_id: int,
) -> dict[str, str]:
    """Get an item from the warehouse."""
    _ = item_id
    return {"message": "Item has been gotten!"}
