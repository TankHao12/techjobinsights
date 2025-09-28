#!/bin/bash

# Script to dump local PostgreSQL database and restore to Supabase

echo "Migrating Database to Supabase (Schema + Data)"
echo "=================================================="

# Configuration
LOCAL_DB="techjobs"
LOCAL_USER="postgres"
DOCKER_CONTAINER="nz-tech-jobs-db"  # From docker-compose.yml

# Check if Docker container is running
if ! docker ps | grep -q "$DOCKER_CONTAINER"; then
    echo "ERROR: Docker container '$DOCKER_CONTAINER' is not running"
    echo "Start it with: docker-compose up database -d"
    exit 1
fi

echo "Docker container is running"

# Get script directory and navigate to backend root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if .env file exists in backend directory
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "ERROR: .env file not found"
    echo "Please create a .env file at $BACKEND_DIR/.env with your Supabase DATABASE_URL"
    exit 1
fi

# Load Supabase connection string
export $(grep -v '^#' "$BACKEND_DIR/.env" | grep DATABASE_URL | xargs)

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set in .env file"
    exit 1
fi

echo "Configuration loaded"
echo ""

# Create backup directory
mkdir -p "$BACKEND_DIR/database/backup"
DUMP_FILE="$BACKEND_DIR/database/backup/db_dump_$(date +%Y%m%d_%H%M%S).sql"

# Step 1: Dump local database
echo "Step 1: Dumping database from Docker container..."
echo "Container: $DOCKER_CONTAINER"
echo "Output: $DUMP_FILE"

# Use docker exec to run pg_dump inside the container (no password needed - uses peer auth)
docker exec $DOCKER_CONTAINER pg_dump -U $LOCAL_USER \
    --no-owner --no-acl --clean --if-exists \
    --format=plain $LOCAL_DB > $DUMP_FILE

if [ $? -ne 0 ]; then
    echo "Failed to dump database from Docker container"
    exit 1
fi

echo "Database dumped successfully"
echo ""

# Step 2: Restore to Supabase
echo "Step 2: Restoring to Supabase..."
echo "WARNING: This will overwrite existing data in Supabase!"
read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    echo "Dump file saved at: $DUMP_FILE"
    exit 1
fi

# Restore to Supabase
psql $DATABASE_URL -f $DUMP_FILE

if [ $? -eq 0 ]; then
    echo "Database restored to Supabase successfully!"
    echo ""
    echo "Backup file saved at: $DUMP_FILE"
else
    echo "Failed to restore database to Supabase"
    echo ""
    echo "If psql is not installed, you can use Docker:"
    echo "docker exec -i $DOCKER_CONTAINER psql \"$DATABASE_URL\" < $DUMP_FILE"
    exit 1
fi
