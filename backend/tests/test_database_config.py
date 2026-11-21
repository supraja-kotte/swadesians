"""Database URL handling for SQLite and PostgreSQL."""

from app.db.connection import normalize_database_url


def test_plain_postgres_url_uses_psycopg_driver() -> None:
    url = "postgresql://farmer:secret@localhost:5432/agriguide"
    assert normalize_database_url(url) == (
        "postgresql+psycopg://farmer:secret@localhost:5432/agriguide"
    )


def test_explicit_driver_and_sqlite_urls_are_unchanged() -> None:
    explicit = "postgresql+psycopg://farmer@localhost/agriguide"
    sqlite = "sqlite:///./agri_guide.db"

    assert normalize_database_url(explicit) == explicit
    assert normalize_database_url(sqlite) == sqlite
