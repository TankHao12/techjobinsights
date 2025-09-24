#!/usr/bin/env python3
"""
Setup Alembic for database migrations

This script initializes Alembic configuration for managing database schema changes.
Alembic allows you to:
- Track schema changes over time
- Apply incremental migrations
- Rollback changes if needed
- Maintain schema history

Usage:
    python database/setup_alembic.py
    # OR from backend root:
    python -m database.setup_alembic
"""

import os
import sys
import subprocess

def main():
    """Initialize Alembic configuration"""
    print("="*80)
    print("ALEMBIC MIGRATION SETUP")
    print("="*80)
    
    # Check if alembic is installed
    try:
        import alembic
        print("✅ Alembic is installed")
    except ImportError:
        print("❌ Alembic is not installed")
        print("📦 Installing Alembic...")
        subprocess.run([sys.executable, "-m", "pip", "install", "alembic"], check=True)
        print("✅ Alembic installed successfully")
    
    # Initialize alembic if not already done
    if not os.path.exists("alembic"):
        print("\n🏗️  Initializing Alembic...")
        subprocess.run(["alembic", "init", "alembic"], check=True)
        print("✅ Alembic initialized")
        
        # Update alembic.ini with database URL
        print("\n📝 Updating alembic.ini configuration...")
        with open("alembic.ini", "r") as f:
            config = f.read()
        
        # Replace the sqlalchemy.url line
        config = config.replace(
            "sqlalchemy.url = driver://user:pass@localhost/dbname",
            "# sqlalchemy.url = driver://user:pass@localhost/dbname\n"
            "# Database URL is set programmatically in env.py from DATABASE_URL environment variable"
        )
        
        with open("alembic.ini", "w") as f:
            f.write(config)
        
        print("✅ alembic.ini updated")
        
        # Update env.py to use our models
        print("\n📝 Updating alembic/env.py to import models...")
        env_py_content = """\"\"\"
Alembic environment configuration
\"\"\"
from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database configuration and models
from app.database import Base, DATABASE_URL
# Import all models so Alembic can detect them
from app.models import (
    RawJob, Job, Company, Skill, JobSkill, Location,
    ScrapingSession, Category, SkillTrend
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from environment
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    \"\"\"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    \"\"\"
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True  # Detect default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        
        with open("alembic/env.py", "w") as f:
            f.write(env_py_content)
        
        print("✅ alembic/env.py updated with model imports")
        
        print("\n" + "="*80)
        print("✅ ALEMBIC SETUP COMPLETE!")
        print("="*80)
        print("\n📋 Next steps:")
        print("   1. Create initial migration:")
        print("      alembic revision --autogenerate -m 'Initial schema'")
        print("   2. Apply migrations:")
        print("      alembic upgrade head")
        print("   3. After changing models, create new migration:")
        print("      alembic revision --autogenerate -m 'Description of changes'")
        print("   4. View migration history:")
        print("      alembic history")
        print("   5. Rollback one migration:")
        print("      alembic downgrade -1")
        print()
    else:
        print("\n✅ Alembic is already initialized")
        print("📋 To create a new migration after model changes:")
        print("   alembic revision --autogenerate -m 'Description'")

if __name__ == "__main__":
    main()

