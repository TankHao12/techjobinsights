#!/bin/bash
# Daily update script for tech jobs insights

echo "=========================================="
echo "STARTING DAILY UPDATE - $(date)"
echo "=========================================="

# Step 1: Scrape new jobs
echo ""
echo "Step 1: Scraping new jobs..."
docker exec nz-tech-jobs-backend python database/operations/incremental_scrape.py --pages 3

# Step 2: Run NLP pipeline (optimized for new jobs)
echo ""
echo "Step 2: Running NLP pipeline (optimized - no redundant URL checking)..."
docker exec nz-tech-jobs-backend python database/operations/run_nlp_pipeline.py

# Step 2.5: Check URLs for older jobs (maintenance)
echo ""
echo "Step 2.5: Checking URLs for older jobs (maintenance)..."
docker exec nz-tech-jobs-backend python database/maintenance/check_existing_job_urls.py --older-than-days 7 --batch-size 30

# Step 3: Verify data
echo ""
echo "Step 3: Verifying data quality..."
docker exec nz-tech-jobs-backend python database/maintenance/verify_data.py

echo ""
echo "=========================================="
echo "DAILY UPDATE COMPLETE - $(date)"
echo "=========================================="