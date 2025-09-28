#!/bin/bash
# Script to initialize Alembic version tracking after running init-db.sql
# 
# Use this when you've deployed a fresh database using init-db.sql
# and want to start tracking future changes with Alembic migrations.

set -e

echo "=============================================="
echo "Alembic Version Stamp Script"
echo "=============================================="
echo ""
echo "This script will mark your database as being"
echo "at the latest Alembic migration version."
echo ""
echo "Use this ONLY if you've just run init-db.sql"
echo "to create a fresh database."
echo ""

# Get the latest migration version
cd "$(dirname "$0")/.."
LATEST_VERSION=$(alembic history | head -n 1 | awk '{print $2}')

echo "Latest migration version: $LATEST_VERSION"
echo ""

# Ask for confirmation
read -p "Stamp database with this version? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Stamp the database
echo "Stamping database..."
alembic stamp head

echo ""
echo "✅ Database stamped successfully!"
echo ""
echo "Next steps:"
echo "1. Make changes to models in app/models/tables.py"
echo "2. Generate migration: alembic revision --autogenerate -m 'Description'"
echo "3. Review migration in alembic/versions/"
echo "4. Apply migration: alembic upgrade head"
