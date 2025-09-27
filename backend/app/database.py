"""
Database configuration and connection management for Tech Jobs Insights NZ

This module provides:
- Database engine configuration
- Session management
- Base class for all ORM models
- Connection utilities
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not installed, skip loading
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@database:5432/techjobs"
)

# Connection arguments for psycopg2 to help with IPv6/IPv4 issues
# This is particularly important for Azure App Service which doesn't support IPv6 outbound
connect_args = {}
if "supabase" in DATABASE_URL.lower():
    # For Supabase connections, ensure SSL and set timeout
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10,
        # Note: keepalives help maintain connection through Azure's network
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
    logger.info("Configuring Supabase connection with SSL and keepalives")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Additional connections beyond pool_size
    connect_args=connect_args  # Pass connection arguments to psycopg2
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
# All models must inherit from this Base class
Base = declarative_base()

def get_db():
    """
    Dependency to get database session.
    Used with FastAPI's dependency injection system.
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

def test_connection():
    """
    Test database connection on startup.
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def create_tables():
    """
    Create all tables in the database.
    Used for development and testing.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise