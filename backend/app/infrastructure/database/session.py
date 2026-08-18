"""Database engine and request-scoped sessions."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def get_database_session() -> Generator[Session, None, None]:
    """Yield a database session and always close it after the request."""
    with SessionFactory() as session:
        yield session
