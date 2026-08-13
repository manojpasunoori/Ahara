from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import get_settings


def create_database_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def check_database_connection(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
