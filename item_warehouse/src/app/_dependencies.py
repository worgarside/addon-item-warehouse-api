from typing import Generator
from sqlalchemy.orm import Session
from logging import getLogger
from item_warehouse.src.app.database import SessionLocal
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel("DEBUG")
add_stream_handler(LOGGER)

def get_db(session_name: str = "") -> Generator[Session, None, None]:
    """Get a database connection, and safely close it when done."""

    db = SessionLocal()
    try:
        yield db
    finally:
        if session_name:
            LOGGER.debug("Closing database connection for %s.", session_name)
        else:
            LOGGER.debug("Closing database connection.")

        db.close()