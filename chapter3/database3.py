"""Database configuration"""

# ─── Imports ───────────────────────────────────────────────────────────
# create_engine: builds the SQLAlchemy "engine" (the connection to the DB)
from sqlalchemy import create_engine

# declarative_base: factory that gives us the Base class our models inherit from
from sqlalchemy.orm import declarative_base

# sessionmaker: factory that creates Session objects (used for queries)
from sqlalchemy.orm import sessionmaker


# ─── Database URL ──────────────────────────────────────────────────────
# Format: "<dialect>:///<path>"
#   sqlite:///   → using SQLite
#   ./fantasy_data.db → file in the same folder as this script
SQLALCHEMY_DATABASE_URL = "sqlite:///./fantasy_data.db"


# ─── Engine ────────────────────────────────────────────────────────────
# The engine is SQLAlchemy's connection manager — it talks to SQLite.
# check_same_thread=False is a SQLite-specific setting that lets multiple
# threads share this connection (FastAPI uses threads, so we need this).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


# ─── Session factory ───────────────────────────────────────────────────
# SessionLocal() will create a new "session" — your handle for one
# conversation with the database (queries, inserts, commits, etc.)
#
# autocommit=False  → you must explicitly commit changes
# autoflush=False   → don't auto-push pending changes mid-query (safer)
# bind=engine       → all sessions use the engine defined above
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── Base class ────────────────────────────────────────────────────────
# Every model class in models.py inherits from Base.
# SQLAlchemy uses this to know which classes map to database tables.
Base = declarative_base()