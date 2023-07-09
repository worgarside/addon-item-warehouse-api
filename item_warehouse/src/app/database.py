"""Database constants and classes."""

from os import environ, getenv

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore[attr-defined]

DATABASE_USERNAME = environ["DATABASE_USERNAME"]
DATABASE_PASSWORD = environ["DATABASE_PASSWORD"]
DATABASE_HOST = getenv("DATABASE_HOST", "homeassistant.local")
DATABASE_PORT = int(getenv("DATABASE_PORT", "3306"))
DATABASE_NAME = getenv("DATABASE_NAME", "item_warehouse")

SQLALCHEMY_DATABASE_URL = f"mariadb+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}?charset=utf8mb4"  # noqa: E501

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
