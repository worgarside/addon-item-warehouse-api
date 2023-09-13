"""Dependency injection for the FastAPI app."""

from __future__ import annotations

from collections.abc import Generator
from logging import getLogger
from os import getenv

from database import SessionLocal
from sqlalchemy.orm import Session
from wg_utilities.loggers import add_stream_handler

LOGGER = getLogger(__name__)
LOGGER.setLevel(getenv("LOG_LEVEL", "DEBUG"))
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
