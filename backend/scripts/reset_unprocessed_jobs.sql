-- Reset processed flag for jobs that exist in raw_jobs but not in jobs table
-- This allows them to be reprocessed by the NLP pipeline

-- First, let's see the current status
SELECT 
    'Current Status' as status,
    COUNT(*) as total_raw_jobs,
    COUNT(CASE WHEN processed = true THEN 1 END) as processed_raw_jobs,
    COUNT(CASE WHEN processed = false OR processed IS NULL THEN 1 END) as unprocessed_raw_jobs,
    (SELECT COUNT(*) FROM jobs) as jobs_in_jobs_table
FROM raw_jobs;

-- Show jobs that are processed but missing from jobs table
SELECT 
    'Jobs processed but missing from jobs table' as description,
    COUNT(*) as count
FROM raw_jobs rj 
LEFT JOIN jobs j ON rj.id = j.raw_job_id 
WHERE rj.processed = true AND j.id IS NULL;

-- Reset processed flag to FALSE for jobs that don't exist in jobs table
-- This will allow them to be reprocessed by the NLP pipeline
UPDATE raw_jobs 
SET 
    processed = false,
    processed_at = NULL,
    processing_version = NULL
WHERE id NOT IN (
    SELECT DISTINCT raw_job_id 
    FROM jobs 
    WHERE raw_job_id IS NOT NULL
);

-- Show the updated status
SELECT 
    'Updated Status' as status,
    COUNT(*) as total_raw_jobs,
    COUNT(CASE WHEN processed = true THEN 1 END) as processed_raw_jobs,
    COUNT(CASE WHEN processed = false OR processed IS NULL THEN 1 END) as unprocessed_raw_jobs,
    (SELECT COUNT(*) FROM jobs) as jobs_in_jobs_table
FROM raw_jobs;

-- Show how many jobs were reset
SELECT 
    'Jobs reset for reprocessing' as description,
    COUNT(*) as count
FROM raw_jobs 
WHERE processed = false AND processed_at IS NULL;
