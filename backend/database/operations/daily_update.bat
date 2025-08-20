@echo off
REM Daily update script for tech jobs insights (Windows)

echo ==========================================
echo STARTING DAILY UPDATE - %date% %time%
echo ==========================================

REM Step 1: Scrape new jobs
echo.
echo Step 1: Scraping new jobs...
docker exec tech-jobs-backend python database/incremental_scrape.py --pages 3

REM Step 2: Run NLP pipeline (now using DataProcessingPipeline)
echo.
echo Step 2: Running NLP pipeline...
docker exec tech-jobs-backend python database/run_nlp_pipeline.py

REM Step 3: Verify data
echo.
echo Step 3: Verifying data quality...
docker exec tech-jobs-backend python database/verify_data.py

echo.
echo ==========================================
echo DAILY UPDATE COMPLETE - %date% %time%
echo ==========================================
