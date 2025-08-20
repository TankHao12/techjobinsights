# Database Operations

Scripts for daily operations and data pipelines.

## Scripts

-   **daily_update.py** - Complete daily update process
    -   Runs scraping + NLP processing
    -   Can be scheduled via cron/Task Scheduler
-   **incremental_scrape.py** - Job scraping
    -   Scrapes new jobs from job boards
    -   Stores in raw_jobs table
-   **run_nlp_pipeline.py** - NLP processing
    -   Processes raw jobs
    -   Extracts skills, locations, etc.
    -   Stores in jobs table

## Usage

### Manual Execution

```bash
# Run complete daily update
python backend/database/operations/daily_update.py

# Or run individual steps
python backend/database/operations/incremental_scrape.py
python backend/database/operations/run_nlp_pipeline.py
```

### Scheduled Execution

**Windows (Task Scheduler):**

```batch
daily_update.bat
```

**Linux (Cron):**

```bash
0 2 * * * /path/to/database/operations/daily_update.sh
```

## Logs

Check logs for execution details and errors.
