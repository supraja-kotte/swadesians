"""Database engine and session setup.

SQLAlchemy lets us write the same Python code for SQLite now and PostgreSQL
later. The only thing that changes is the DATABASE_URL in `.env`.
"""

from sqlalchemy import create_engine
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


def init_db() -> None:
    """Create tables if needed, then add clearly labelled demo content once."""
    from app.models import admin, assistant, community, equipment, marketplace, profile, schemes, smart_farming, videos  # noqa: F401  (imports register tables)

    Base.metadata.create_all(bind=engine)

    from app.db.seed import seed_demo_community
    from app.db.seed_assistant import seed_demo_commands
    from app.db.seed_equipment import seed_demo_equipment
    from app.db.seed_marketplace import seed_demo_marketplace
    from app.db.seed_scheme_links import seed_verified_scheme_links
    from app.db.seed_schemes import seed_demo_scheme_topics
    from app.db.seed_smart_farming import seed_demo_smart_topics
    from app.db.seed_videos import seed_demo_videos

    seed_demo_community()
    seed_demo_commands()
    seed_demo_equipment()
    seed_demo_marketplace()
    seed_demo_scheme_topics()
    seed_verified_scheme_links()
    seed_demo_smart_topics()
    seed_demo_videos()
