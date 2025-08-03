-- ============================================================================
-- TechInsights  - Database Initialization Script
-- Run this script to set up the database for development
-- ============================================================================

-- Create database user if not exists (for development)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'techinsights') THEN
        CREATE ROLE techinsights WITH LOGIN PASSWORD 'dev_password_123';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE techinsights_dev TO techinsights;
GRANT USAGE, CREATE ON SCHEMA public TO techinsights;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO techinsights;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO techinsights;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO techinsights;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO techinsights;

-- Create development-specific settings
SET TIME ZONE 'Pacific/Auckland';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TechInsights  database initialized successfully';
    RAISE NOTICE 'Time zone set to: %', current_setting('TIMEZONE');
    RAISE NOTICE 'Database ready for development';
END
$$;