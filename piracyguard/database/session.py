"""Database session management for AI-PiracyGuard.

Provides thread-safe session factory with connection pooling.
Supports SQLite (development) and PostgreSQL (production).
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from piracyguard.database.models import Base
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

# Module-level engine and session factory (lazy initialization)
_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """Create or return the SQLAlchemy engine.

    Uses connection pooling appropriate for the database backend:
    - SQLite: StaticPool (single connection, thread-safe with check_same_thread=False)
    - PostgreSQL/MySQL: QueuePool with configurable size

    Args:
        database_url: Database connection string. If None, reads from
                      DATABASE_URL env var or defaults to SQLite.

    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine

    if _engine is not None:
        return _engine

    if database_url is None:
        database_url = os.environ.get(
            "DATABASE_URL",
            "sqlite:///database/piracyguard.db",
        )

    is_sqlite = database_url.startswith("sqlite")

    if is_sqlite:
        # SQLite: use StaticPool for thread safety
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        )

        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    else:
        # PostgreSQL/MySQL: use QueuePool with connection recycling
        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=True,
            echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        )

    logger.info(
        "Database engine created",
        extra={"database_url": database_url.split("@")[-1] if "@" in database_url else database_url},
    )

    return _engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker:
    """Get or create the session factory.

    Args:
        engine: SQLAlchemy Engine. If None, uses get_engine().

    Returns:
        Configured sessionmaker instance.
    """
    global _SessionFactory

    if _SessionFactory is not None:
        return _SessionFactory

    if engine is None:
        engine = get_engine()

    _SessionFactory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    return _SessionFactory


def get_session() -> Session:
    """Create a new database session.

    Returns:
        New SQLAlchemy Session instance.

    Note:
        Caller is responsible for closing the session.
        Prefer using the `session_scope()` context manager instead.
    """
    factory = get_session_factory()
    return factory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic rollback on error.

    Usage:
        with session_scope() as session:
            user = User(username="admin")
            session.add(user)
            # Auto-commits on successful exit
            # Auto-rolls-back on exception

    Yields:
        SQLAlchemy Session instance.
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(database_url: str | None = None, drop_all: bool = False) -> None:
    """Initialize the database — create all tables.

    Args:
        database_url: Database connection string. If None, uses default.
        drop_all: If True, drops all existing tables first (DANGEROUS).
    """
    engine = get_engine(database_url)

    if drop_all:
        logger.warning("Dropping all database tables!")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def reset_engine() -> None:
    """Reset the engine and session factory (useful for testing)."""
    global _engine, _SessionFactory

    if _engine is not None:
        _engine.dispose()
        _engine = None
    _SessionFactory = None
