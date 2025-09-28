#!/bin/bash

# Script to dump PostgreSQL database from Docker and restore to Supabase
# This version uses Docker for BOTH dumping and restoring (no local psql/pg_dump required)

echo "Migrating Database to Supabase (Schema + Data)"
echo "=================================================="
echo "Using Docker for all operations"
echo ""

# Configuration
LOCAL_DB="techjobs"
LOCAL_USER="postgres"
DOCKER_CONTAINER="nz-tech-jobs-db"  # From docker-compose.yml

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "Docker is running"

# Check if Docker container is running
if ! docker ps | grep -q "$DOCKER_CONTAINER"; then
    echo "ERROR: Docker container '$DOCKER_CONTAINER' is not running"
    echo "Start it with: docker-compose up database -d"
    exit 1
fi

echo "Database container is running"

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

echo "Supabase configuration loaded"
echo ""

# Create backup directory
mkdir -p "$BACKEND_DIR/database/backup"
DUMP_FILE="$BACKEND_DIR/database/backup/db_dump_$(date +%Y%m%d_%H%M%S).sql"

# Step 1: Dump database from Docker container
echo "Step 1: Dumping database from Docker container..."
echo "Container: $DOCKER_CONTAINER"
echo "Database: $LOCAL_DB"
echo "Output: $DUMP_FILE"
echo ""

docker exec $DOCKER_CONTAINER pg_dump -U $LOCAL_USER \
    --no-owner --no-acl --clean --if-exists \
    --format=plain $LOCAL_DB > $DUMP_FILE

if [ $? -ne 0 ]; then
    echo "Failed to dump database from Docker container"
    exit 1
fi

# Check dump file size
DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo "Database dumped successfully ($DUMP_SIZE)"
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

# Restore using Docker container (works even if psql not installed locally)
echo "Restoring to Supabase using Docker..."
docker exec -i $DOCKER_CONTAINER psql "$DATABASE_URL" < $DUMP_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "Database restored to Supabase successfully!"
    echo ""
    echo "Summary:"
    echo "  - Dump file: $DUMP_FILE"
    echo "  - Size: $DUMP_SIZE"
    echo "  - Source: Docker container ($DOCKER_CONTAINER)"
    echo "  - Destination: Supabase"
else
    echo ""
    echo "Failed to restore database to Supabase"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check your Supabase DATABASE_URL in .env"
    echo "2. Verify your Supabase password is correct"
    echo "3. Check if your IP is allowed in Supabase (Settings → Database)"
    echo "4. Try adding '?sslmode=require' to your DATABASE_URL"
    echo ""
    echo "Dump file saved at: $DUMP_FILE"
    exit 1
fi
