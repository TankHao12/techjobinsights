-- =============================================================================
-- Tech Jobs Insights NZ Database Initialization Script
-- =============================================================================
-- This script creates the complete database schema for the tech jobs platform
-- 
-- Database: techjobs
-- PostgreSQL Version: 17+
-- Updated: October 2025
-- 
-- IMPORTANT NOTES:
-- - This script reflects the CURRENT schema as of October 2025
-- - Schema is managed by Alembic migrations in production
-- - Use this script ONLY for:
--   1. Fresh Azure deployments
--   2. Development environment resets
--   3. Testing/staging environments
-- - For production schema changes, ALWAYS use Alembic migrations
-- =============================================================================

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

-- Enable UUID generation (for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search with trigram similarity
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- CUSTOM TYPES (PostgreSQL ENUMs)
-- =============================================================================
-- These match the Python Enums in backend/app/models/enums.py

-- Employment types enum
CREATE TYPE employment_type AS ENUM (
    'full_time',
    'part_time',
    'contract',
    'internship',
    'not_specified'
);

-- Experience levels enum  
CREATE TYPE experience_level AS ENUM (
    'entry',
    'junior',
    'mid',
    'senior',
    'lead',
    'principal',
    'executive',
    'not_specified'
);

-- Work arrangement enum
CREATE TYPE work_arrangement AS ENUM (
    'remote',
    'hybrid',
    'onsite',
    'flexible',
    'not_specified'
);

-- =============================================================================
-- CORE TABLES - STAGE 1: RAW DATA COLLECTION
-- =============================================================================

-- Raw Jobs Table (Scraped Data - Unprocessed)
CREATE TABLE raw_jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    full_description TEXT,
    location TEXT,  -- Raw location text from scraper
    posting_date TEXT,  -- As scraped (unparsed)
    search_term TEXT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_version TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CORE TABLES - STAGE 2: NORMALIZED DATA
-- =============================================================================

-- Companies Table (Simplified - Name Only)
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT UNIQUE NOT NULL,  -- For case-insensitive matching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations Table
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    region TEXT,  -- 'North Island', 'South Island'
    country TEXT DEFAULT 'New Zealand',
    total_jobs INTEGER DEFAULT 0,
    avg_salary INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Categories Table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color_code TEXT,  -- Hex color for UI
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs Table (Processed Job Data - Core Entity)
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    raw_job_id INTEGER REFERENCES raw_jobs(id) ON DELETE CASCADE,
    
    -- ========================================================================
    -- CORE JOB INFORMATION
    -- ========================================================================
    title TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    
    -- ========================================================================
    -- DATES - Posted date passed directly from raw_jobs.posting_date
    -- ========================================================================
    posted_date DATE,  -- Passed from raw_jobs, not NLP parsed
    scraped_at TIMESTAMP,
    
    -- ========================================================================
    -- NLP CLASSIFICATION RESULTS
    -- ========================================================================
    is_tech_job BOOLEAN DEFAULT TRUE,
    tech_confidence_score DECIMAL(3,2),
    
    -- ========================================================================
    -- JOB DETAILS (NLP Extracted) - Using Enums
    -- ========================================================================
    employment_type employment_type DEFAULT 'not_specified',
    experience_level experience_level,
    work_arrangement work_arrangement DEFAULT 'not_specified',
    
    -- ========================================================================
    -- SKILLS - Single JSONB field for simplicity
    -- Format: {"languages": ["Python", "Java"], "frameworks": ["Django", "React"]}
    -- ========================================================================
    extracted_skills JSONB,  -- Grouped by category
    
    -- ========================================================================
    -- SALARY INFORMATION
    -- ========================================================================
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT DEFAULT 'NZD',
    salary_period TEXT,  -- 'year', 'month', 'hour'
    salary_raw_text TEXT,  -- Original salary text for reference
    salary_confidence_score DECIMAL(3,2),
    
    -- ========================================================================
    -- PROCESSING METADATA
    -- ========================================================================
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_version TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- ========================================================================
    -- TRACEABILITY
    -- ========================================================================
    original_url TEXT,
    found_via_search_term TEXT,
    
    -- Constraints
    CONSTRAINT check_salary_range CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max),
    CONSTRAINT check_positive_salary CHECK (salary_min IS NULL OR salary_min > 0)
);

-- =============================================================================
-- ANALYTICS TABLE (Currently Unused - Reserved for Future)
-- =============================================================================

-- Skill Trends Table (Time Series)
-- Note: This table exists in schema but is not currently populated
-- Reserved for future analytics dashboard features
CREATE TABLE skill_trends (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER,  -- References removed - no skills table
    date_recorded DATE NOT NULL,
    job_count INTEGER DEFAULT 0,
    new_jobs_count INTEGER DEFAULT 0,
    avg_salary DECIMAL(10, 2),
    demand_score DECIMAL(5, 2),  -- Calculated metric
    growth_percentage DECIMAL(5, 2),
    
    CONSTRAINT check_job_count_positive CHECK (job_count >= 0),
    CONSTRAINT check_new_jobs_positive CHECK (new_jobs_count >= 0)
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Raw Jobs indexes
CREATE INDEX idx_raw_jobs_url ON raw_jobs(url);
CREATE INDEX idx_raw_jobs_processed ON raw_jobs(processed);
CREATE INDEX idx_raw_jobs_scraped_at ON raw_jobs(scraped_at);

-- Jobs table indexes
CREATE INDEX idx_jobs_raw_job_id ON jobs(raw_job_id);
CREATE INDEX idx_jobs_company_id ON jobs(company_id);
CREATE INDEX idx_jobs_location_id ON jobs(location_id);
CREATE INDEX idx_jobs_category_id ON jobs(category_id);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX idx_jobs_is_active ON jobs(is_active);
CREATE INDEX idx_jobs_salary_min ON jobs(salary_min);
CREATE INDEX idx_jobs_employment_type ON jobs(employment_type);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_work_arrangement ON jobs(work_arrangement);

-- JSONB index for extracted_skills
CREATE INDEX idx_jobs_extracted_skills ON jobs USING gin(extracted_skills);

-- Companies indexes
CREATE INDEX idx_companies_normalized_name ON companies(normalized_name);

-- Locations indexes
CREATE INDEX idx_locations_city ON locations(city);
CREATE INDEX idx_locations_region ON locations(region);

-- Text search indexes
CREATE INDEX idx_jobs_title_text ON jobs USING gin(to_tsvector('english', title));
CREATE INDEX idx_jobs_description_text ON jobs USING gin(to_tsvector('english', description));

-- Similarity search indexes
CREATE INDEX idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

-- =============================================================================
-- SEED DATA - INITIAL REFERENCE DATA
-- =============================================================================

-- Insert default NZ locations
INSERT INTO locations (city, region) VALUES 
('Auckland', 'North Island'),
('Wellington', 'North Island'),
('Christchurch', 'South Island'),
('Hamilton', 'North Island'),
('Tauranga', 'North Island'),
('Dunedin', 'South Island'),
('Palmerston North', 'North Island'),
('Nelson', 'South Island'),
('Rotorua', 'North Island'),
('New Plymouth', 'North Island'),
('Napier', 'North Island'),
('Queenstown', 'South Island'),
('Remote', 'National')
ON CONFLICT DO NOTHING;

-- Insert job categories
INSERT INTO categories (name, description, color_code, sort_order) VALUES 
('Frontend Development', 'User interface and user experience development', '#3B82F6', 1),
('Backend Development', 'Server-side development and APIs', '#10B981', 2),
('Full Stack Development', 'Both frontend and backend development', '#8B5CF6', 3),
('Mobile Development', 'iOS and Android application development', '#F59E0B', 4),
('DevOps & Infrastructure', 'CI/CD, cloud infrastructure, and automation', '#EF4444', 5),
('Data Science & Analytics', 'Data analysis, machine learning, and AI', '#06B6D4', 6),
('Quality Assurance', 'Software testing and quality assurance', '#84CC16', 7),
('Product Management', 'Product strategy and management', '#F97316', 8),
('Security & Compliance', 'Cybersecurity and regulatory compliance', '#DC2626', 9),
('Project Management', 'Technical project and program management', '#7C3AED', 10),
('UI/UX Design', 'User interface and user experience design', '#EC4899', 11),
('Database Administration', 'Database design, optimization, and management', '#059669', 12),
('Software Engineering', 'General software development', '#6366F1', 13),
('Cloud Architecture', 'Cloud solutions and architecture', '#14B8A6', 14),
('Technical Leadership', 'Tech lead and architecture roles', '#F43F5E', 15)
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for active jobs with company and location details
CREATE OR REPLACE VIEW active_jobs_view AS
SELECT 
    j.id,
    j.title,
    c.name as company_name,
    l.city,
    l.region,
    cat.name as category,
    j.salary_min,
    j.salary_max,
    j.employment_type,
    j.experience_level,
    j.work_arrangement,
    j.posted_date,
    j.original_url,
    j.extracted_skills
FROM jobs j
LEFT JOIN companies c ON j.company_id = c.id
LEFT JOIN locations l ON j.location_id = l.id
LEFT JOIN categories cat ON j.category_id = cat.id
WHERE j.is_active = true;

-- View for location statistics
CREATE OR REPLACE VIEW location_stats_view AS
SELECT 
    l.id,
    l.city,
    l.region,
    COUNT(j.id) as total_jobs,
    AVG(j.salary_max) as avg_max_salary,
    AVG(j.salary_min) as avg_min_salary,
    COUNT(CASE WHEN j.work_arrangement = 'remote' THEN 1 END) as remote_jobs,
    COUNT(CASE WHEN j.work_arrangement = 'hybrid' THEN 1 END) as hybrid_jobs,
    COUNT(CASE WHEN j.work_arrangement = 'onsite' THEN 1 END) as onsite_jobs
FROM locations l
LEFT JOIN jobs j ON l.id = j.location_id AND j.is_active = true
GROUP BY l.id, l.city, l.region
ORDER BY total_jobs DESC;

-- View for category statistics
CREATE OR REPLACE VIEW category_stats_view AS
SELECT 
    c.id,
    c.name,
    c.color_code,
    COUNT(j.id) as total_jobs,
    AVG(j.salary_max) as avg_max_salary,
    COUNT(CASE WHEN j.employment_type = 'full_time' THEN 1 END) as full_time_jobs,
    COUNT(CASE WHEN j.employment_type = 'contract' THEN 1 END) as contract_jobs
FROM categories c
LEFT JOIN jobs j ON c.id = j.category_id AND j.is_active = true
GROUP BY c.id, c.name, c.color_code
ORDER BY total_jobs DESC;

-- =============================================================================
-- ALEMBIC VERSION TABLE
-- =============================================================================
-- This table is managed by Alembic for migration tracking
-- It will be created automatically when you run: alembic upgrade head
-- DO NOT manually insert records into this table

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

-- Insert a record to track initialization
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run Alembic migrations if using version control: alembic upgrade head';
    RAISE NOTICE '2. Start scraping jobs: python backend/database/incremental_scrape.py';
    RAISE NOTICE '3. Process scraped jobs: python backend/database/run_nlp_pipeline.py';
END $$;
