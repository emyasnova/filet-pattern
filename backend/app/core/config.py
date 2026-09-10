"""Application settings loaded from the repository environment file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from sqlalchemy import URL, make_url

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Runtime settings shared by the API and migration tooling."""

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "filet_pattern"
    postgres_user: str = "filet"
    postgres_password: str = "filet"
    database_url: str | None = None
    frontend_dist_dir: Path = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    public_origin: str | None = None
    canonical_host: str | None = None
    pattern_creation_enabled: bool = False
    public_read_rate_limit: int = 120

    @field_validator("database_url")
    @classmethod
    def empty_database_url_is_unset(cls, value: str | None) -> str | None:
        """Treat an empty deployment variable like an omitted value."""
        return value or None

    @property
    def sqlalchemy_database_url(self) -> URL:
        """Prefer DATABASE_URL and force PostgreSQL to use psycopg 3."""
        if self.database_url:
            url = make_url(self.database_url)
            if url.drivername in {"postgres", "postgresql"} or url.drivername.startswith(
                "postgresql+"
            ):
                url = url.set(drivername="postgresql+psycopg")
            return url
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def allowed_hosts(self) -> list[str]:
        """Return configured deployment hosts, or allow all in local development."""
        hosts = {host for host in (self.canonical_host,) if host}
        if self.canonical_host:
            hosts.add(f"www.{self.canonical_host}")
        if self.public_origin:
            hosts.add(make_url(self.public_origin).host or "")
        hosts.discard("")
        return sorted(hosts) or ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
