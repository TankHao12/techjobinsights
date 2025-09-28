#!/bin/bash

# Script to deploy database schema to Supabase using Alembic migrations

echo "Deploying Database Schema to Supabase"
echo "========================================="

# Get script directory and navigate to backend root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if .env file exists in backend directory
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "ERROR: .env file not found in backend directory"
    echo "Please create a .env file at $BACKEND_DIR/.env with your Supabase DATABASE_URL"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$BACKEND_DIR/.env" | xargs)

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set in .env file"
    exit 1
fi

echo "Environment variables loaded"
echo ""

# Check current migration status
echo "Checking current migration status..."
alembic current
echo ""

# Show pending migrations
echo "Pending migrations:"
alembic history
echo ""

# Ask for confirmation
read -p "Do you want to apply migrations to Supabase? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Database schema deployed successfully!"
    echo ""
    echo "Current migration version:"
    alembic current
else
    echo "Migration failed!"
    exit 1
fi
