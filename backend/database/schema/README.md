# Database Schema

This folder contains all schema-related files.

## Files

-   **init.py** - Python-based schema initialization

    -   Creates tables from SQLAlchemy models
    -   Loads seed data
    -   Used in development

-   **init-db.sql** - SQL-based schema initialization

    -   Complete SQL schema definition
    -   Used for Azure/production deployment
    -   Kept in sync with models

-   **setup_alembic.py** - Alembic migration setup

    -   Initializes Alembic for migration tracking
    -   Run once per environment

-   **stamp_alembic.bat/sh** - Helper scripts
    -   Stamps database after using init-db.sql
    -   Tells Alembic schema is up-to-date

## Usage

### Development Setup

```bash
cd backend
python database/schema/init.py --seed-data
```

### Production Deployment (Azure)

```bash
psql -h your-server.postgres.database.azure.com \
     -U admin -d techjobs \
     -f database/schema/init-db.sql

# Then mark Alembic as current
cd backend
alembic stamp head
# Or use: ./database/schema/stamp_alembic.bat
```

### Setting Up Migrations

```bash
python database/schema/setup_alembic.py
```

## Documentation

See `../docs/INIT_SCRIPT.md` for detailed usage guide.
