"""Database engine and session setup.

SQLAlchemy lets us write the same Python code for SQLite now and PostgreSQL
later. The only thing that changes is the DATABASE_URL in `.env`.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL


def normalize_database_url(url: str) -> str:
    """Use psycopg 3 for plain postgresql:// URLs without changing the user's DSN."""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
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
    """Create tables if needed, then add clearly labelled demo content once."""
    from app.models import admin, assistant, community, equipment, marketplace, profile, schemes, smart_farming, videos  # noqa: F401  (imports register tables)

    Base.metadata.create_all(bind=engine)
    ensure_schema()

    from app.db.seed import seed_demo_community
    from app.db.seed_assistant import seed_demo_commands
    from app.db.seed_equipment import seed_demo_equipment
    from app.db.seed_marketplace import seed_demo_marketplace
    from app.db.seed_scheme_links import seed_verified_scheme_links
    from app.db.seed_schemes import seed_demo_scheme_topics
    from app.db.seed_smart_farming import seed_demo_smart_topics, seed_verified_smart_videos
    from app.db.seed_videos import seed_demo_videos

    seed_demo_community()
    seed_demo_commands()
    seed_demo_equipment()
    seed_demo_marketplace()
    seed_demo_scheme_topics()
    seed_verified_scheme_links()
    seed_demo_smart_topics()
    seed_verified_smart_videos()
    seed_demo_videos()
