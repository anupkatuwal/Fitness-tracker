"""SQLAlchemy 2.0 engine, session factory and declarative base."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _engine_kwargs() -> dict:
    url = settings.sqlalchemy_url
    if url.startswith("sqlite"):
        # SQLite needs this to be usable from FastAPI's threadpool.
        return {"connect_args": {"check_same_thread": False}}
    # MS SQL Server: pre-ping so stale pooled connections are recycled.
    return {"pool_pre_ping": True, "pool_recycle": 1800, "fast_executemany": True}


engine = create_engine(settings.sqlalchemy_url, echo=settings.db_echo, **_engine_kwargs())

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for local development and tests.

    In production this is a no-op on purpose: the schema is owned by Alembic
    (``alembic upgrade head``). ``create_all`` only ever creates missing
    tables — it never alters an existing one — so relying on it in production
    silently leaves the database behind the models the first time a column
    changes.
    """
    from app import models  # noqa: F401  (registers the mappers)

    if settings.is_production:
        logger.info("Production mode: schema is managed by Alembic, skipping create_all.")
        return

    Base.metadata.create_all(bind=engine)
