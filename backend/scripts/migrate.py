"""Create any missing database tables for the configured DATABASE_URL.

This is a deliberate first migration step: it is safe for SQLite and for a new
PostgreSQL database. It does NOT yet alter columns in an existing PostgreSQL
database. Alembic should be added before making schema changes to live data.

Run from `agri-guide/backend`:
    .\\.venv\\Scripts\\python.exe -m scripts.migrate
"""

from app.db.connection import engine, init_db, normalize_database_url
from app.config import DATABASE_URL


def main() -> None:
    print(f"Database URL: {normalize_database_url(DATABASE_URL)}")
    init_db()
    print("Tables are up to date.")
    print(f"Engine: {engine.dialect.name}")


if __name__ == "__main__":
    main()
