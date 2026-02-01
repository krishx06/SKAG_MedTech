"""
Database connection and session management for AdaptiveCare.

Uses SQLAlchemy with SQLite for development and PostgreSQL for production.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from backend.core.config import Config

logger = logging.getLogger(__name__)

# Create declarative base for ORM models
Base = declarative_base()

# Database engine
engine = None
SessionLocal = None


def init_db(database_url: str = None):
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    db_url = database_url or Config.DATABASE_URL if hasattr(Config, 'DATABASE_URL') else "sqlite:///./adaptivecare.db"
    
    logger.info(f"Initializing database: {db_url}")
    
    # SQLite specific configuration
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=Config.DEBUG if hasattr(Config, 'DEBUG') else False
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL or other databases
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=Config.DEBUG if hasattr(Config, 'DEBUG') else False
        )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")
    return engine


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection.
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    if SessionLocal is None:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Session:
    """Get a database session (non-generator version)."""
    if SessionLocal is None:
        init_db()
    return SessionLocal()


# Initialize on module import if config available
try:
    if not engine:
        init_db()
except Exception as e:
    logger.warning(f"Database not initialized on import: {e}")
