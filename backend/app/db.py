from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """FastAPI dependency — yields a session scoped to a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """Standalone session context for background tasks, WebSockets, and workers.

    Usage::

        from app.db import db_session

        with db_session() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
