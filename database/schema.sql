-- ============================================================================
-- TechInsights  - Enhanced Database Schema
-- PostgreSQL 15+ Required
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- ============================================================================
-- CUSTOM TYPES AND ENUMS
-- ============================================================================

-- Experience level classification
CREATE TYPE experience_level_enum AS ENUM (
    'Entry', 'Junior', 'Mid', 'Senior', 'Lead', 'Principal', 'Executive'
);

-- Employment type classification
CREATE TYPE employment_type_enum AS ENUM (
    'Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Casual'
);

-- Remote work options
CREATE TYPE remote_work_enum AS ENUM (
    'On-site', 'Remote', 'Hybrid', 'Flexible'
);

-- Technology requirement type
CREATE TYPE requirement_type_enum AS ENUM (
    'required', 'preferred', 'nice-to-have', 'mentioned'
);

-- ============================================================================
-- DATA SOURCES MANAGEMENT
-- ============================================================================

CREATE TABLE data_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE NOT NULL, -- 'seek', 'indeed', 'linkedin', 'trademe'
    base_url VARCHAR(255),
    api_endpoint VARCHAR(255),
    scraping_config JSONB, -- Store source-specific configuration
    rate_limit_per_hour INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    last_scraped_at TIMESTAMP,
    total_jobs_collected INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Comments for documentation
COMMENT ON TABLE data_sources IS 'Configuration and metadata for job data sources';
COMMENT ON COLUMN data_sources.scraping_config IS 'JSON configuration for source-specific scraping parameters';
COMMENT ON COLUMN data_sources.rate_limit_per_hour IS 'Maximum requests per hour to avoid rate limiting';

-- ============================================================================
-- COMPANIES AND ORGANIZATIONS
-- ============================================================================

CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255), -- For deduplication across sources
    company_size VARCHAR(50), -- 'startup', 'small', 'medium', 'large', 'enterprise'
    industry VARCHAR(100),
    website_url VARCHAR(255),
    linkedin_url VARCHAR(255),
    description TEXT,
    logo_url VARCHAR(255),
    location VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(50) DEFAULT 'New Zealand',
    founded_year INTEGER,
    employee_count_min INTEGER,
    employee_count_max INTEGER,
    glassdoor_rating DECIMAL(2,1),
    total_jobs_posted INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_normalized_company UNIQUE(normalized_name),
    CONSTRAINT valid_employee_count CHECK (employee_count_max >= employee_count_min),
    CONSTRAINT valid_founded_year CHECK (founded_year >= 1800 AND founded_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    CONSTRAINT valid_glassdoor_rating CHECK (glassdoor_rating >= 1.0 AND glassdoor_rating <= 5.0)
);

COMMENT ON TABLE companies IS 'Company profiles aggregated from multiple sources';
COMMENT ON COLUMN companies.normalized_name IS 'Standardized company name for deduplication';
COMMENT ON COLUMN companies.is_verified IS 'Whether company information has been manually verified';

-- Indexes for company search and analytics
CREATE INDEX idx_companies_name ON companies(normalized_name);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_size ON companies(company_size);
CREATE INDEX idx_companies_location ON companies(city, country);

-- Full-text search index for company names
CREATE INDEX idx_companies_name_search ON companies 
USING GIN(to_tsvector('english', company_name || ' ' || COALESCE(normalized_name, '')));

-- ============================================================================
-- JOB CATEGORIES AND CLASSIFICATIONS
-- ============================================================================

CREATE TABLE job_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INTEGER REFERENCES job_categories(category_id),
    source_id INTEGER REFERENCES data_sources(source_id),
    external_category_id VARCHAR(50), -- Original category ID from source
    description TEXT,
    is_tech_related BOOLEAN DEFAULT true,
    job_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_category_per_source UNIQUE(source_id, external_category_id)
);

COMMENT ON TABLE job_categories IS 'Hierarchical job categorization from various sources';
COMMENT ON COLUMN job_categories.external_category_id IS 'Original category identifier from the source platform';

-- Index for category hierarchy queries
CREATE INDEX idx_job_categories_parent ON job_categories(parent_category_id);
CREATE INDEX idx_job_categories_source ON job_categories(source_id);

-- ============================================================================
-- TECHNOLOGY STACKS AND SKILLS
-- ============================================================================

CREATE TABLE tech_stacks (
    tech_id SERIAL PRIMARY KEY,
    technology_name VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL, -- Standardized name for analysis
    category VARCHAR(50) NOT NULL, -- 'Frontend', 'Backend', 'Database', 'Cloud', 'DevOps', 'Mobile', 'AI/ML'
    subcategory VARCHAR(50), -- More specific categorization
    aliases TEXT[], -- Array of alternative names and spellings
    popularity_score DECIMAL(5,2) DEFAULT 0.00, -- Global popularity metric
    learning_difficulty VARCHAR(20), -- 'Easy', 'Medium', 'Hard'
    market_demand VARCHAR(20), -- 'Low', 'Medium', 'High', 'Very High'
    description TEXT,
    official_website VARCHAR(255),
    documentation_url VARCHAR(255),
    is_programming_language BOOLEAN DEFAULT false,
    is_framework BOOLEAN DEFAULT false,
    is_tool BOOLEAN DEFAULT false,
    is_database BOOLEAN DEFAULT false,
    is_cloud_service BOOLEAN DEFAULT false,
    release_year INTEGER,
    latest_version VARCHAR(50),
    license_type VARCHAR(100),
    github_url VARCHAR(255),
    stackoverflow_tag VARCHAR(100),
    job_mentions_count INTEGER DEFAULT 0,
    last_updated_stats TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_tech_name UNIQUE(normalized_name),
    CONSTRAINT valid_popularity_score CHECK (popularity_score >= 0 AND popularity_score <= 100),
    CONSTRAINT valid_release_year CHECK (release_year >= 1950 AND release_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 5)
);

COMMENT ON TABLE tech_stacks IS 'Comprehensive technology and skills database';
COMMENT ON COLUMN tech_stacks.aliases IS 'Alternative names and common misspellings for technology matching';
COMMENT ON COLUMN tech_stacks.popularity_score IS 'Calculated score based on job mentions, GitHub stars, Stack Overflow activity';

-- Indexes for tech stacks
CREATE INDEX idx_tech_stacks_category ON tech_stacks(category);
CREATE INDEX idx_tech_stacks_popularity ON tech_stacks(popularity_score DESC);
CREATE INDEX idx_tech_stacks_type ON tech_stacks(is_programming_language, is_framework, is_tool);

-- GIN index for array operations on aliases
CREATE INDEX idx_tech_stacks_aliases ON tech_stacks USING GIN(aliases);

-- Full-text search index for technology names and aliases
CREATE INDEX idx_tech_stacks_name_search ON tech_stacks 
USING GIN(to_tsvector('english', technology_name || ' ' || COALESCE(array_to_string(aliases, ' '), '')));

-- ============================================================================
-- CORE JOB DATA
-- ============================================================================

CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    external_job_id VARCHAR(255) NOT NULL, -- Original job ID from source
    source_id INTEGER NOT NULL REFERENCES data_sources(source_id),
    company_id INTEGER REFERENCES companies(company_id),
    
    -- Job Details
    title VARCHAR(500) NOT NULL,
    description_raw TEXT, -- Original HTML/formatted description
    description_cleaned TEXT, -- Cleaned text for analysis
    summary TEXT, -- Brief job summary (first 500 chars)
    
    -- Location and Work Arrangement
    location VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(50) DEFAULT 'New Zealand',
    postal_code VARCHAR(20),
    is_remote_friendly BOOLEAN DEFAULT false,
    remote_work_option remote_work_enum,
    
    -- Compensation
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(10) DEFAULT 'NZD',
    salary_period VARCHAR(20), -- 'hourly', 'daily', 'weekly', 'monthly', 'annually'
    salary_is_negotiable BOOLEAN DEFAULT false,
    
    -- Job Classification
    experience_level experience_level_enum,
    employment_type employment_type_enum,
    category_id INTEGER REFERENCES job_categories(category_id),
    seniority_level INTEGER, -- 1-10 scale
    
    -- URLs and References
    job_url VARCHAR(1000),
    application_url VARCHAR(1000),
    company_url VARCHAR(1000),
    
    -- Dates and Timing
    posted_date TIMESTAMP,
    expires_date TIMESTAMP,
    last_seen_date TIMESTAMP, -- When we last saw this job active
    application_deadline TIMESTAMP,
    
    -- Data Quality and Processing
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'archived'
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    completeness_score DECIMAL(3,2), -- How complete the job data is
    
    -- Content Analysis
    word_count INTEGER,
    required_tech_count INTEGER DEFAULT 0,
    preferred_tech_count INTEGER DEFAULT 0,
    benefits_mentioned TEXT[],
    perks_mentioned TEXT[],
    
    -- Status and Management
    is_active BOOLEAN DEFAULT true,
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of INTEGER REFERENCES jobs(job_id),
    is_featured BOOLEAN DEFAULT false,
    is_urgent BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    apply_count INTEGER DEFAULT 0,
    
    -- Metadata
    raw_data JSONB, -- Store original JSON for debugging
    extraction_metadata JSONB, -- Store extraction process metadata
    
    -- Constraints
    CONSTRAINT unique_job_per_source UNIQUE(external_job_id, source_id),
    CONSTRAINT valid_salary_range CHECK (salary_max >= salary_min),
    CONSTRAINT valid_dates CHECK (expires_date >= posted_date),
    CONSTRAINT valid_seniority_level CHECK (seniority_level >= 1 AND seniority_level <= 10)
);

COMMENT ON TABLE jobs IS 'Normalized job postings from all data sources';
COMMENT ON COLUMN jobs.data_quality_score IS 'Calculated score based on data completeness and accuracy';
COMMENT ON COLUMN jobs.raw_data IS 'Original job posting data for debugging and reprocessing';

-- Performance indexes for jobs table
CREATE INDEX idx_jobs_source_id ON jobs(source_id);
CREATE INDEX idx_jobs_company_id ON jobs(company_id);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_location ON jobs(city, country);
CREATE INDEX idx_jobs_active ON jobs(is_active) WHERE is_active = true;
CREATE INDEX idx_jobs_processing_status ON jobs(processing_status);
CREATE INDEX idx_jobs_salary_range ON jobs(salary_min, salary_max) WHERE salary_min IS NOT NULL;

-- Full-text search indexes
CREATE INDEX idx_jobs_description_fts ON jobs 
USING GIN(to_tsvector('english', COALESCE(description_cleaned, '')));

CREATE INDEX idx_jobs_title_fts ON jobs 
USING GIN(to_tsvector('english', COALESCE(title, '')));

-- Composite indexes for common queries
CREATE INDEX idx_jobs_active_posted ON jobs(is_active, posted_date DESC) 
WHERE is_active = true;

CREATE INDEX idx_jobs_source_active_posted ON jobs(source_id, is_active, posted_date DESC) 
WHERE is_active = true;

CREATE INDEX idx_jobs_location_active ON jobs(city, is_active, posted_date DESC)
WHERE is_active = true;

-- ============================================================================
-- JOB-TECHNOLOGY RELATIONSHIPS
-- ============================================================================

CREATE TABLE job_tech_requirements (
    requirement_id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    tech_id INTEGER NOT NULL REFERENCES tech_stacks(tech_id),
    
    requirement_type requirement_type_enum DEFAULT 'mentioned',
    confidence_score DECIMAL(3,2) DEFAULT 0.50 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    years_experience INTEGER,
    proficiency_level VARCHAR(20), -- 'Beginner', 'Intermediate', 'Advanced', 'Expert'
    is_primary_skill BOOLEAN DEFAULT false,
    
    -- Context information
    context_snippet TEXT, -- Where/how this tech was mentioned
    position_in_description INTEGER, -- Order of appearance in job description
    mention_count INTEGER DEFAULT 1, -- How many times mentioned
    
    -- Detection metadata
    detection_method VARCHAR(50), -- 'keyword', 'ml_classifier', 'manual', 'pattern_match'
    detection_confidence DECIMAL(3,2), -- Confidence in the detection method
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by VARCHAR(100), -- System or user who verified
    is_verified BOOLEAN DEFAULT false,
    
    -- Relationship metadata
    importance_score DECIMAL(3,2), -- How important this skill is for the job
    market_value_score DECIMAL(3,2), -- Market value of this skill
    
    CONSTRAINT unique_job_tech UNIQUE(job_id, tech_id),
    CONSTRAINT valid_years_experience CHECK (years_experience >= 0 AND years_experience <= 50),
    CONSTRAINT valid_position CHECK (position_in_description > 0)
);

COMMENT ON TABLE job_tech_requirements IS 'Technology requirements for jobs with ML-enhanced detection';
COMMENT ON COLUMN job_tech_requirements.confidence_score IS 'ML confidence in requirement classification';
COMMENT ON COLUMN job_tech_requirements.detection_method IS 'Method used to detect this technology requirement';

-- Indexes for job-tech relationships
CREATE INDEX idx_job_tech_requirements_job_id ON job_tech_requirements(job_id);
CREATE INDEX idx_job_tech_requirements_tech_id ON job_tech_requirements(tech_id);
CREATE INDEX idx_job_tech_requirements_type ON job_tech_requirements(requirement_type);
CREATE INDEX idx_job_tech_requirements_confidence ON job_tech_requirements(confidence_score DESC);
CREATE INDEX idx_job_tech_requirements_primary ON job_tech_requirements(is_primary_skill) 
WHERE is_primary_skill = true;

-- Composite index for analytics queries
CREATE INDEX idx_job_tech_analytics ON job_tech_requirements(tech_id, requirement_type, confidence_score);

-- ============================================================================
-- ANALYTICS AND TRENDS
-- ============================================================================

CREATE TABLE tech_trend_analytics (
    trend_id SERIAL PRIMARY KEY,
    tech_id INTEGER NOT NULL REFERENCES tech_stacks(tech_id),
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'quarterly'
    
    -- Metrics
    job_count INTEGER NOT NULL DEFAULT 0,
    total_jobs_in_period INTEGER NOT NULL DEFAULT 0,
    percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    growth_rate DECIMAL(5,2), -- Compared to previous period
    velocity DECIMAL(5,2), -- Rate of change
    rank_position INTEGER, -- Ranking within category for this period
    rank_change INTEGER, -- Change in ranking from previous period
    
    -- Filters applied
    experience_level experience_level_enum,
    location_filter VARCHAR(255),
    source_filter INTEGER REFERENCES data_sources(source_id),
    category_filter VARCHAR(50),
    
    -- Statistical data
    avg_salary_min DECIMAL(10,2),
    avg_salary_max DECIMAL(10,2),
    median_salary DECIMAL(10,2),
    salary_growth_rate DECIMAL(5,2),
    
    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(50) DEFAULT 'automated',
    data_points_used INTEGER,
    confidence_interval DECIMAL(5,2),
    
    CONSTRAINT unique_trend_period UNIQUE(tech_id, period_start, period_end, 
                                        COALESCE(experience_level::text, ''), 
                                        COALESCE(location_filter, ''), 
                                        COALESCE(source_filter::text, '')),
    CONSTRAINT valid_percentage CHECK (percentage >= 0 AND percentage <= 100),
    CONSTRAINT valid_period CHECK (period_end >= period_start)
);

COMMENT ON TABLE tech_trend_analytics IS 'Pre-computed technology trend analytics for performance';
COMMENT ON COLUMN tech_trend_analytics.velocity IS 'Rate of change in demand over time';

-- Indexes for analytics
CREATE INDEX idx_tech_trend_analytics_tech_id ON tech_trend_analytics(tech_id);
CREATE INDEX idx_tech_trend_analytics_period ON tech_trend_analytics(period_start, period_end);
CREATE INDEX idx_tech_trend_analytics_percentage ON tech_trend_analytics(percentage DESC);
CREATE INDEX idx_tech_trend_analytics_growth ON tech_trend_analytics(growth_rate DESC);
CREATE INDEX idx_tech_trend_analytics_rank ON tech_trend_analytics(rank_position ASC);

-- ============================================================================
-- COMPANY TECH PROFILES
-- ============================================================================

CREATE TABLE company_tech_profiles (
    profile_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    tech_id INTEGER NOT NULL REFERENCES tech_stacks(tech_id),
    
    -- Metrics
    job_count INTEGER NOT NULL DEFAULT 0,
    total_company_jobs INTEGER NOT NULL DEFAULT 0,
    usage_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    
    -- Analysis period
    analysis_period_start DATE NOT NULL,
    analysis_period_end DATE NOT NULL,
    
    -- Tech adoption info
    first_mentioned_date DATE,
    last_mentioned_date DATE,
    adoption_trend VARCHAR(20), -- 'increasing', 'stable', 'decreasing', 'emerging', 'declining'
    adoption_velocity DECIMAL(5,2), -- Rate of adoption change
    
    -- Position within company
    avg_requirement_type DECIMAL(3,2), -- Average requirement strength
    is_core_technology BOOLEAN DEFAULT false,
    is_emerging_technology BOOLEAN DEFAULT false,
    
    -- Salary impact
    avg_salary_premium DECIMAL(5,2), -- Salary premium for this tech
    salary_impact_score DECIMAL(3,2),
    
    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_company_tech_period UNIQUE(company_id, tech_id, analysis_period_start, analysis_period_end),
    CONSTRAINT valid_usage_percentage CHECK (usage_percentage >= 0 AND usage_percentage <= 100)
);

COMMENT ON TABLE company_tech_profiles IS 'Technology adoption profiles for companies';
COMMENT ON COLUMN company_tech_profiles.is_core_technology IS 'Whether this technology is core to the companys tech stack';

-- ============================================================================
-- DATA QUALITY AND MONITORING
-- ============================================================================

CREATE TABLE data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(source_id),
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Collection metrics
    jobs_collected INTEGER DEFAULT 0,
    jobs_processed INTEGER DEFAULT 0,
    jobs_failed INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    
    -- Quality metrics
    avg_quality_score DECIMAL(3,2),
    duplicate_rate DECIMAL(5,2),
    missing_description_rate DECIMAL(5,2),
    missing_company_rate DECIMAL(5,2),
    missing_location_rate DECIMAL(5,2),
    missing_salary_rate DECIMAL(5,2),
    
    -- Processing metrics
    tech_detection_rate DECIMAL(5,2),
    avg_tech_per_job DECIMAL(5,2),
    processing_time_avg_seconds DECIMAL(8,2),
    ml_confidence_avg DECIMAL(3,2),
    
    -- Performance metrics
    api_response_time_avg DECIMAL(8,2),
    scraping_success_rate DECIMAL(5,2),
    rate_limit_hits INTEGER DEFAULT 0,
    
    -- Error tracking
    error_count INTEGER DEFAULT 0,
    error_details JSONB,
    warnings_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_source_date UNIQUE(source_id, metric_date)
);

COMMENT ON TABLE data_quality_metrics IS 'Daily data quality and performance metrics';

-- ============================================================================
-- AUDIT AND CHANGE TRACKING
-- ============================================================================

CREATE TABLE audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[], -- Array of field names that changed
    changed_by VARCHAR(100), -- System user or process
    change_reason TEXT,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all data changes';

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at DESC);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_changed_by ON audit_log(changed_by);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION VIEWS
-- ============================================================================

-- View for jobs with enriched data
CREATE VIEW jobs_enriched AS
SELECT 
    j.*,
    c.company_name as company_full_name,
    c.company_size,
    c.industry,
    c.glassdoor_rating,
    ds.source_name,
    jc.category_name,
    jc.is_tech_related,
    ARRAY_AGG(DISTINCT ts.technology_name) FILTER (WHERE ts.technology_name IS NOT NULL) as technologies,
    ARRAY_AGG(DISTINCT ts.category) FILTER (WHERE ts.category IS NOT NULL) as tech_categories,
    COUNT(jtr.tech_id) as tech_count,
    AVG(jtr.confidence_score) as avg_tech_confidence,
    COUNT(CASE WHEN jtr.requirement_type = 'required' THEN 1 END) as required_tech_count,
    COUNT(CASE WHEN jtr.requirement_type = 'preferred' THEN 1 END) as preferred_tech_count
FROM jobs j
LEFT JOIN companies c ON j.company_id = c.company_id
LEFT JOIN data_sources ds ON j.source_id = ds.source_id
LEFT JOIN job_categories jc ON j.category_id = jc.category_id
LEFT JOIN job_tech_requirements jtr ON j.job_id = jtr.job_id
LEFT JOIN tech_stacks ts ON jtr.tech_id = ts.tech_id
WHERE j.is_active = true
GROUP BY j.job_id, c.company_id, ds.source_id, jc.category_id;

COMMENT ON VIEW jobs_enriched IS 'Jobs with aggregated company, tech, and category information';

-- View for current tech trends
CREATE VIEW current_tech_trends AS
SELECT 
    ts.technology_name,
    ts.category,
    ts.popularity_score,
    tta.percentage,
    tta.growth_rate,
    tta.rank_position,
    tta.job_count,
    tta.period_start,
    tta.period_end
FROM tech_trend_analytics tta
JOIN tech_stacks ts ON tta.tech_id = ts.tech_id
WHERE tta.period_start >= CURRENT_DATE - INTERVAL '30 days'
    AND tta.experience_level IS NULL
    AND tta.location_filter IS NULL
    AND tta.source_filter IS NULL
ORDER BY tta.percentage DESC;

COMMENT ON VIEW current_tech_trends IS 'Current technology trends for the last 30 days';

-- ============================================================================
-- FUNCTIONS FOR DATA MAINTENANCE
-- ============================================================================

-- Function to update job quality scores
CREATE OR REPLACE FUNCTION update_job_quality_score(job_row_id INTEGER)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    quality_score DECIMAL(3,2) := 0.0;
    job_record RECORD;
BEGIN
    SELECT * INTO job_record FROM jobs WHERE job_id = job_row_id;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Check description completeness (25% weight)
    IF LENGTH(COALESCE(job_record.description_cleaned, '')) > 100 THEN
        quality_score := quality_score + 0.25;
    END IF;
    
    -- Check company information (20% weight)
    IF job_record.company_id IS NOT NULL THEN
        quality_score := quality_score + 0.20;
    END IF;
    
    -- Check salary information (15% weight)
    IF job_record.salary_min IS NOT NULL AND job_record.salary_max IS NOT NULL THEN
        quality_score := quality_score + 0.15;
    END IF;
    
    -- Check location information (15% weight)
    IF LENGTH(COALESCE(job_record.location, '')) > 0 THEN
        quality_score := quality_score + 0.15;
    END IF;
    
    -- Check date freshness (15% weight)
    IF job_record.posted_date IS NOT NULL AND 
       job_record.posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN
        quality_score := quality_score + 0.15;
    END IF;
    
    -- Check tech requirements (10% weight)
    IF EXISTS (SELECT 1 FROM job_tech_requirements WHERE job_id = job_row_id) THEN
        quality_score := quality_score + 0.10;
    END IF;
    
    -- Update the job record
    UPDATE jobs SET 
        data_quality_score = quality_score,
        last_updated = CURRENT_TIMESTAMP
    WHERE job_id = job_row_id;
    
    RETURN quality_score;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_job_quality_score IS 'Calculate and update data quality score for a job';

-- Function to normalize company names
CREATE OR REPLACE FUNCTION normalize_company_name(company_name_input TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(company_name_input, '\s+(Ltd|Limited|Inc|Corporation|Corp|Pty|Co)\.?\s*$', '', 'i'),
                '[^a-zA-Z0-9\s]', '', 'g'
            )
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION normalize_company_name IS 'Normalize company names for deduplication';

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers to relevant tables
CREATE TRIGGER update_companies_modtime 
    BEFORE UPDATE ON companies 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_jobs_modtime 
    BEFORE UPDATE ON jobs 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_tech_stacks_modtime 
    BEFORE UPDATE ON tech_stacks 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_data_sources_modtime 
    BEFORE UPDATE ON data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Trigger to normalize company names on insert/update
CREATE OR REPLACE FUNCTION trigger_normalize_company_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_name = normalize_company_name(NEW.company_name);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER normalize_company_name_trigger
    BEFORE INSERT OR UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION trigger_normalize_company_name();

-- ============================================================================
-- INITIAL DATA SEEDING
-- ============================================================================

-- Insert default data sources
INSERT INTO data_sources (source_name, base_url, api_endpoint, rate_limit_per_hour, scraping_config) VALUES
('seek', 'https://www.seek.co.nz', 'https://www.seek.co.nz/api/jobsearch/v5/search', 100, '{"classification": "6281", "pageSize": 22}'),
('indeed', 'https://nz.indeed.com', 'https://nz.indeed.com/jobs', 50, '{"country": "NZ", "sort": "date"}'),
('linkedin', 'https://www.linkedin.com', 'https://api.linkedin.com/v2/jobs', 25, '{"location": "New Zealand", "industry": "technology"}'),
('trademe', 'https://www.trademe.co.nz', 'https://api.trademe.co.nz/v1/Jobs', 75, '{"category": "5023"}');

-- Insert common technology categories and stacks
INSERT INTO tech_stacks (technology_name, normalized_name, category, is_programming_language, is_framework, description) VALUES
-- Programming Languages
('JavaScript', 'javascript', 'Frontend', true, false, 'Dynamic programming language for web development'),
('TypeScript', 'typescript', 'Frontend', true, false, 'Typed superset of JavaScript'),
('Python', 'python', 'Backend', true, false, 'High-level programming language'),
('Java', 'java', 'Backend', true, false, 'Object-oriented programming language'),
('C#', 'csharp', 'Backend', true, false, 'Microsoft .NET programming language'),
('Go', 'go', 'Backend', true, false, 'Google systems programming language'),
('Rust', 'rust', 'Backend', true, false, 'Systems programming language'),
('Kotlin', 'kotlin', 'Mobile', true, false, 'JVM programming language for Android'),
('Swift', 'swift', 'Mobile', true, false, 'Apple programming language for iOS'),

-- Frontend Frameworks
('React', 'react', 'Frontend', false, true, 'JavaScript library for building user interfaces'),
('Vue.js', 'vue', 'Frontend', false, true, 'Progressive JavaScript framework'),
('Angular', 'angular', 'Frontend', false, true, 'TypeScript-based web application framework'),
('Svelte', 'svelte', 'Frontend', false, true, 'Compile-time web framework'),
('Next.js', 'nextjs', 'Frontend', false, true, 'React-based web framework'),

-- Backend Frameworks
('Node.js', 'nodejs', 'Backend', false, true, 'JavaScript runtime for server-side development'),
('Django', 'django', 'Backend', false, true, 'Python web framework'),
('Flask', 'flask', 'Backend', false, true, 'Micro web framework for Python'),
('FastAPI', 'fastapi', 'Backend', false, true, 'Modern Python web framework'),
('Spring Boot', 'spring-boot', 'Backend', false, true, 'Java application framework'),
('ASP.NET Core', 'aspnet-core', 'Backend', false, true, 'Microsoft web framework'),

-- Databases
('PostgreSQL', 'postgresql', 'Database', false, false, 'Advanced open source relational database'),
('MySQL', 'mysql', 'Database', false, false, 'Popular open source relational database'),
('MongoDB', 'mongodb', 'Database', false, false, 'Document-oriented NoSQL database'),
('Redis', 'redis', 'Database', false, false, 'In-memory data structure store'),
('SQLite', 'sqlite', 'Database', false, false, 'Lightweight embedded database'),

-- Cloud Services
('AWS', 'aws', 'Cloud', false, false, 'Amazon Web Services cloud platform'),
('Azure', 'azure', 'Cloud', false, false, 'Microsoft cloud computing platform'),
('Google Cloud', 'gcp', 'Cloud', false, false, 'Google Cloud Platform'),
('Kubernetes', 'kubernetes', 'DevOps', false, false, 'Container orchestration platform'),
('Docker', 'docker', 'DevOps', false, false, 'Containerization platform'),

-- DevOps Tools
('Git', 'git', 'DevOps', false, false, 'Distributed version control system'),
('GitHub', 'github', 'DevOps', false, false, 'Git repository hosting service'),
('GitLab', 'gitlab', 'DevOps', false, false, 'Git repository management platform'),
('Jenkins', 'jenkins', 'DevOps', false, false, 'Automation server for CI/CD'),
('Terraform', 'terraform', 'DevOps', false, false, 'Infrastructure as code tool');

-- Update aliases for common technologies
UPDATE tech_stacks SET aliases = ARRAY['js', 'ecmascript'] WHERE normalized_name = 'javascript';
UPDATE tech_stacks SET aliases = ARRAY['ts'] WHERE normalized_name = 'typescript';
UPDATE tech_stacks SET aliases = ARRAY['reactjs', 'react.js'] WHERE normalized_name = 'react';
UPDATE tech_stacks SET aliases = ARRAY['vuejs', 'vue.js'] WHERE normalized_name = 'vue';
UPDATE tech_stacks SET aliases = ARRAY['angularjs', 'angular.js'] WHERE normalized_name = 'angular';
UPDATE tech_stacks SET aliases = ARRAY['node', 'nodejs'] WHERE normalized_name = 'nodejs';
UPDATE tech_stacks SET aliases = ARRAY['postgres', 'psql'] WHERE normalized_name = 'postgresql';
UPDATE tech_stacks SET aliases = ARRAY['k8s', 'kube'] WHERE normalized_name = 'kubernetes';
UPDATE tech_stacks SET aliases = ARRAY['c-sharp', 'c sharp', 'csharp', 'c#'] WHERE normalized_name = 'csharp';

-- Create initial job categories
INSERT INTO job_categories (category_name, description, is_tech_related) VALUES
('Software Development', 'Software engineering and development roles', true),
('Data Science & Analytics', 'Data analysis, machine learning, and AI roles', true),
('DevOps & Infrastructure', 'System administration and DevOps roles', true),
('Product Management', 'Product and project management roles', true),
('UX/UI Design', 'User experience and interface design roles', true),
('Quality Assurance', 'Software testing and QA roles', true),
('Cybersecurity', 'Information security and cybersecurity roles', true),
('Mobile Development', 'iOS and Android development roles', true),
('Frontend Development', 'Frontend and client-side development roles', true),
('Backend Development', 'Backend and server-side development roles', true);

COMMENT ON SCHEMA public IS 'TechInsights  - Enhanced multi-source job market intelligence platform';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================