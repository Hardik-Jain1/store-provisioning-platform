"""
Database Session Management

Provides database initialization and session management.
The database is the source of truth for all store state.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import logging

from models.store import Base
from config import Config

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None


def init_db():
    """
    Initialize the database engine and create all tables.
    Must be called before any database operations.
    """
    global _engine, _session_factory
    
    logger.info(f"Initializing database: {Config.DATABASE_URL}")
    
    # Create engine
    _engine = create_engine(
        Config.DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using
    )
    
    # Create all tables
    Base.metadata.create_all(_engine)
    logger.info("Database tables created successfully")
    
    # Create session factory
    _session_factory = scoped_session(
        sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    )
    
    return _engine


def get_db_session():
    """
    Get a database session.
    Returns a scoped session that is thread-safe.
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


@contextmanager
def session_scope():
    """
    Provide a transactional scope for database operations.
    
    Usage:
        with session_scope() as session:
            store = session.query(Store).filter_by(id='abc').first()
            # ... do work ...
            # Commit happens automatically on success
            # Rollback happens automatically on exception
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        session.close()
