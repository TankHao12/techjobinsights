-- ============================================================================
-- TechInsights  - Sample/Seed Data
-- Initial data for development and testing
-- ============================================================================

-- Insert sample data sources
INSERT INTO data_sources (source_name, base_url, api_endpoint, rate_limit_per_hour, is_active) VALUES
('seek', 'https://www.seek.co.nz', 'https://www.seek.co.nz/api/jobsearch/v5/search', 100, true),
('indeed', 'https://nz.indeed.com', NULL, 50, true),
('trademe', 'https://api.trademe.co.nz/v1', 'https://api.trademe.co.nz/v1/jobs/search.json', 75, true),
('linkedin', 'https://www.linkedin.com', NULL, 25, false);

-- Insert sample technology stacks
INSERT INTO tech_stacks (tech_name, category, subcategory, description, is_active) VALUES
-- Programming Languages
('Python', 'Programming Language', 'Backend', 'High-level programming language', true),
('JavaScript', 'Programming Language', 'Frontend/Backend', 'Dynamic programming language', true),
('TypeScript', 'Programming Language', 'Frontend/Backend', 'Typed superset of JavaScript', true),
('Java', 'Programming Language', 'Backend', 'Object-oriented programming language', true),
('C#', 'Programming Language', 'Backend', 'Microsoft .NET programming language', true),
('Go', 'Programming Language', 'Backend', 'Google programming language', true),
('Rust', 'Programming Language', 'Systems', 'Systems programming language', true),
('PHP', 'Programming Language', 'Backend', 'Server-side scripting language', true),

-- Frontend Frameworks
('React', 'Framework', 'Frontend', 'JavaScript library for building user interfaces', true),
('Angular', 'Framework', 'Frontend', 'TypeScript-based web application framework', true),
('Vue.js', 'Framework', 'Frontend', 'Progressive JavaScript framework', true),
('Svelte', 'Framework', 'Frontend', 'Compile-time optimized framework', true),

-- Backend Frameworks
('Django', 'Framework', 'Backend', 'Python web framework', true),
('Flask', 'Framework', 'Backend', 'Lightweight Python web framework', true),
('FastAPI', 'Framework', 'Backend', 'Modern Python web framework', true),
('Express.js', 'Framework', 'Backend', 'Node.js web application framework', true),
('Spring Boot', 'Framework', 'Backend', 'Java application framework', true),
('ASP.NET Core', 'Framework', 'Backend', '.NET web framework', true),

-- Databases
('PostgreSQL', 'Database', 'SQL', 'Advanced open source relational database', true),
('MySQL', 'Database', 'SQL', 'Popular open source relational database', true),
('MongoDB', 'Database', 'NoSQL', 'Document-oriented database', true),
('Redis', 'Database', 'Cache', 'In-memory data structure store', true),
('SQLite', 'Database', 'SQL', 'Lightweight relational database', true),

-- Cloud Platforms
('AWS', 'Cloud Platform', 'Infrastructure', 'Amazon Web Services', true),
('Azure', 'Cloud Platform', 'Infrastructure', 'Microsoft Azure', true),
('Google Cloud', 'Cloud Platform', 'Infrastructure', 'Google Cloud Platform', true),

-- DevOps Tools
('Docker', 'DevOps', 'Containerization', 'Container platform', true),
('Kubernetes', 'DevOps', 'Orchestration', 'Container orchestration', true),
('Jenkins', 'DevOps', 'CI/CD', 'Automation server', true),
('GitHub Actions', 'DevOps', 'CI/CD', 'GitHub automation platform', true);

-- Insert sample companies
INSERT INTO companies (company_name, normalized_name, company_size, industry, website_url, city, country) VALUES
('Xero', 'xero', 'large', 'Financial Technology', 'https://www.xero.com', 'Wellington', 'New Zealand'),
('Trade Me', 'trademe', 'large', 'E-commerce', 'https://www.trademe.co.nz', 'Wellington', 'New Zealand'),
('Kiwibank', 'kiwibank', 'large', 'Banking', 'https://www.kiwibank.co.nz', 'Wellington', 'New Zealand'),
('Atlassian', 'atlassian', 'large', 'Software Development Tools', 'https://www.atlassian.com', 'Auckland', 'New Zealand'),
('Datacom', 'datacom', 'large', 'IT Services', 'https://www.datacom.com', 'Auckland', 'New Zealand'),
('Spark Ventures', 'spark-ventures', 'medium', 'Telecommunications', 'https://www.sparkventures.co.nz', 'Auckland', 'New Zealand');

-- Add indexes for better performance (if not already in schema)
-- These are likely already in schema.sql but good to ensure
CREATE INDEX IF NOT EXISTS idx_tech_stacks_category ON tech_stacks(category);
CREATE INDEX IF NOT EXISTS idx_tech_stacks_name ON tech_stacks(tech_name);
CREATE INDEX IF NOT EXISTS idx_companies_normalized ON companies(normalized_name);

-- Insert initial analytics data (empty but structure ready)
-- This helps test analytics endpoints
INSERT INTO tech_trend_analytics (tech_id, period_start, period_end, job_count, percentage, growth_rate, rank_position) 
SELECT 
    ts.tech_id,
    CURRENT_DATE - INTERVAL '30 days' as period_start,
    CURRENT_DATE as period_end,
    0 as job_count,
    0.0 as percentage,
    0.0 as growth_rate,
    1 as rank_position
FROM tech_stacks ts 
WHERE ts.is_active = true
LIMIT 10;

-- Log successful seed data insertion
INSERT INTO system_logs (log_level, message, metadata) VALUES 
('INFO', 'Seed data successfully inserted', '{"tables": ["data_sources", "tech_stacks", "companies", "tech_trend_analytics"], "timestamp": "' || CURRENT_TIMESTAMP || '"}');

COMMIT;