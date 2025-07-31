"""
TechInsights  - Database Configuration
SQLAlchemy database setup and session management
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# SYNCHRONOUS DATABASE SETUP
# ============================================================================

# Create synchronous engine
sync_engine = create_engine(
    settings.database_url_sync,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour
    echo=settings.DATABASE_ECHO,
    echo_pool=settings.is_development,
    future=True
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    future=True
)

# ============================================================================
# ASYNCHRONOUS DATABASE SETUP
# ============================================================================

# Create asynchronous engine
async_engine = create_async_engine(
    settings.database_url_async,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour
    echo=settings.DATABASE_ECHO,
    echo_pool=settings.is_development,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ============================================================================
# DATABASE EVENT LISTENERS
# ============================================================================

@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if 'sqlite' in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log database connection checkout."""
    if settings.is_development:
        logger.debug("Database connection checked out")

@event.listens_for(sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log database connection checkin."""
    if settings.is_development:
        logger.debug("Database connection checked in")

# ============================================================================
# SESSION DEPENDENCY FUNCTIONS
# ============================================================================

def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session for FastAPI routes.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

@asynccontextmanager
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Async database transaction error: {e}")
            await session.rollback()
            raise

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def create_all_tables():
    """Create all tables in the database."""
    from src.models import Base
    
    logger.info("Creating all database tables...")
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")

def drop_all_tables():
    """Drop all tables in the database."""
    from src.models import Base
    
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=sync_engine)
    logger.warning("Database tables dropped")

async def create_all_tables_async():
    """Create all tables in the database asynchronously."""
    from src.models import Base
    
    async with async_engine.begin() as conn:
        logger.info("Creating all database tables asynchronously...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

async def drop_all_tables_async():
    """Drop all tables in the database asynchronously."""
    from src.models import Base
    
    async with async_engine.begin() as conn:
        logger.warning("Dropping all database tables asynchronously...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")

def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with sync_engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def check_database_connection_async() -> bool:
    """
    Check if async database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with async_engine.connect() as connection:
            await connection.execute("SELECT 1")
        logger.info("Async database connection successful")
        return True
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        return False

def get_database_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database connection details
    """
    return {
        "url": settings.DATABASE_URL,
        "host": settings.DATABASE_HOST,
        "port": settings.DATABASE_PORT,
        "database": settings.DATABASE_NAME,
        "user": settings.DATABASE_USER,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "echo": settings.DATABASE_ECHO
    }

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_database():
    """Initialize database connection and check health."""
    logger.info("Initializing database connection...")
    
    # Check connection
    if not check_database_connection():
        raise RuntimeError("Failed to connect to database")
    
    logger.info(f"Database initialized: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")

async def initialize_database_async():
    """Initialize async database connection and check health."""
    logger.info("Initializing async database connection...")
    
    # Check connection
    if not await check_database_connection_async():
        raise RuntimeError("Failed to connect to async database")
    
    logger.info(f"Async database initialized: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")

def cleanup_database():
    """Cleanup database connections."""
    logger.info("Cleaning up database connections...")
    sync_engine.dispose()
    logger.info("Database cleanup completed")

async def cleanup_database_async():
    """Cleanup async database connections."""
    logger.info("Cleaning up async database connections...")
    await async_engine.dispose()
    logger.info("Async database cleanup completed")

