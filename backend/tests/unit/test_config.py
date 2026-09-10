"""Runtime database configuration tests."""

from app.core.config import Settings


def test_database_url_has_priority_and_uses_psycopg() -> None:
    settings = Settings(
        database_url="postgresql://cloud:secret@db.example/catalog",
        postgres_host="ignored",
    )
    url = settings.sqlalchemy_database_url
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "db.example"
    assert url.username == "cloud"


def test_postgres_fields_are_fallback() -> None:
    settings = Settings(
        database_url=None,
        postgres_host="postgres",
        postgres_port=55432,
        postgres_db="catalog",
        postgres_user="local",
        postgres_password="secret",
    )
    url = settings.sqlalchemy_database_url
    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.database, url.username) == (
        "postgres", 55432, "catalog", "local"
    )


def test_existing_postgresql_driver_is_replaced() -> None:
    settings = Settings(database_url="postgresql+psycopg2://u:p@host/db")
    assert settings.sqlalchemy_database_url.drivername == "postgresql+psycopg"
