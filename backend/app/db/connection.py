"""Database engine and session setup.

SQLAlchemy lets us write the same Python code for SQLite now and PostgreSQL
later. The only thing that changes is the DATABASE_URL in `.env`.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import DATABASE_URL


def normalize_database_url(url: str) -> str:
    """Use psycopg 3 for plain Postgres URLs without changing the user's DSN.

    Hosting platforms often hand out ``postgres://...`` while SQLAlchemy 2
    expects ``postgresql://...``. Accept both spellings so a copied connection
    string works without manual editing.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


database_url = normalize_database_url(DATABASE_URL)
is_sqlite = database_url.startswith("sqlite")

engine_options: dict = {"pool_pre_ping": True}
if is_sqlite:
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    # Recycle connections that a hosting provider may close silently.
    engine_options["pool_recycle"] = 1800

engine = create_engine(database_url, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Small additive migrations for databases created before owner-submitted
# equipment listings existed. create_all() adds new tables but never alters an
# old table, so these columns are added explicitly and safely.
EQUIPMENT_SCHEMA_ADDITIONS: dict[str, dict[str, str]] = {
    "equipment_listings": {
        "owner_contact": "VARCHAR(120) DEFAULT '' NOT NULL",
        "owner_key_hash": "VARCHAR(64) DEFAULT '' NOT NULL",
        "availability": "VARCHAR(120) DEFAULT '' NOT NULL",
        "status": "VARCHAR(20) DEFAULT 'active' NOT NULL",
    },
    "equipment_enquiries": {
        "farmer_key_hash": "VARCHAR(64) DEFAULT '' NOT NULL",
        "owner_reply": "VARCHAR(300) DEFAULT '' NOT NULL",
    },
}


def ensure_schema() -> None:
    """Add missing equipment columns to an existing database."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    for table, columns in EQUIPMENT_SCHEMA_ADDITIONS.items():
        if table not in tables:
            continue
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, definition in columns.items():
            if name not in existing:
                with engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def init_db() -> None:
    """Create tables and seed only verified or structural (non-demo) content."""
    from app.models import admin, assistant, community, equipment, farmer, profile, schemes, smart_farming  # noqa: F401  (imports register tables)

    Base.metadata.create_all(bind=engine)
    ensure_schema()

    from app.db.seed_assistant import seed_navigation_commands
    from app.db.seed_scheme_links import seed_verified_scheme_links
    from app.db.seed_schemes import seed_guidance_topics
    from app.db.seed_smart_farming import seed_smart_topics, seed_verified_smart_videos

    seed_navigation_commands()
    seed_guidance_topics()
    seed_verified_scheme_links()
    seed_smart_topics()
    seed_verified_smart_videos()
