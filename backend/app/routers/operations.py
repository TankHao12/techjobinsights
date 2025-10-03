"""
Operations Router - Automated Task Endpoints

This module provides API endpoints for automated operations including:
- Incremental job scraping
- NLP pipeline processing
- URL checking for job postings
- Data verification

These endpoints are designed to be called by scheduled tasks (e.g., GitHub Actions)
for daily data updates and maintenance.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import sys
import os

# Add database operations path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))

from app.database import get_db, SessionLocal
from app.models import RawJob, Job
from app.processors.data_pipeline import DataProcessingPipeline
from app.processors.url_checker import URLChecker
from app.scrapers.seek_scraper import SeekScraper
from app.core.logging import get_logger
from sqlalchemy import func, text

logger = get_logger(__name__)

router = APIRouter(
    prefix="/operations",
    tags=["operations"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)


# Pydantic models for request/response
class OperationResponse(BaseModel):
    """Standard response model for operation endpoints"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class ScrapeRequest(BaseModel):
    """Request model for scraping operations"""
    pages_per_term: int = Field(default=3, ge=1, le=20, description="Number of pages to scrape per search term")
    search_terms: Optional[List[str]] = Field(default=None, description="Specific search terms to use")
    stop_on_old_jobs: bool = Field(default=True, description="Stop when encountering old jobs")


class URLCheckRequest(BaseModel):
    """Request model for URL checking operations"""
    older_than_days: int = Field(default=7, ge=1, description="Check jobs older than N days")
    batch_size: int = Field(default=30, ge=1, le=100, description="Number of jobs to check per batch")
    limit: Optional[int] = Field(default=None, ge=1, description="Maximum number of jobs to check")


# Helper function to run scraping
def run_scraping_task(pages: int, search_terms: Optional[List[str]], stop_on_old_jobs: bool) -> Dict[str, Any]:
    """
    Run incremental scrape operation
    
    Args:
        pages: Number of pages to scrape per term
        search_terms: Optional list of search terms
        stop_on_old_jobs: Whether to stop on old jobs
        
    Returns:
        Dictionary with scraping statistics
    """
    try:
        # Import here to avoid module-level import issues
        import sys
        import os
        backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        sys.path.insert(0, backend_path)
        
        from database.operations.incremental_scrape import IncrementalJobScraper
        
        logger.info(f"Starting incremental scrape: pages={pages}, terms={len(search_terms) if search_terms else 'all'}")
        
        scraper = IncrementalJobScraper()
        
        try:
            scraper.run_incremental_scrape(
                search_terms=search_terms,
                max_pages_per_term=pages,
                stop_on_old_jobs=stop_on_old_jobs
            )
            
            return {
                "total_collected": scraper.total_collected,
                "total_saved": scraper.total_saved,
                "duplicates_skipped": scraper.duplicates_skipped,
                "pages_per_term": pages,
                "search_terms_used": len(search_terms) if search_terms else "all"
            }
        finally:
            scraper.cleanup()
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        raise


@router.post("/scrape", response_model=OperationResponse)
async def run_incremental_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(default=False, description="Run in background mode (returns immediately)")
) -> OperationResponse:
    """
    Run incremental job scraping operation
    
    This endpoint scrapes new jobs from Seek NZ that have been posted since the last scrape.
    It's designed to be run daily to keep the job database up to date.
    
    Args:
        request: Scraping parameters
        background_tasks: FastAPI background tasks
        async_mode: If True, runs in background and returns immediately
        
    Returns:
        OperationResponse with scraping statistics (or status if async)
        
    Example:
        POST /api/v1/operations/scrape?async_mode=true
        {
            "pages_per_term": 3,
            "stop_on_old_jobs": true
        }
    """
    try:
        logger.info(f"Scrape operation requested: pages={request.pages_per_term}, async={async_mode}")
        
        if async_mode:
            # Run in background, return immediately
            def scrape_in_background():
                try:
                    stats = run_scraping_task(
                        pages=request.pages_per_term,
                        search_terms=request.search_terms,
                        stop_on_old_jobs=request.stop_on_old_jobs
                    )
                    logger.info(f"Background scraping completed: {stats['total_saved']} new jobs")
                except Exception as e:
                    logger.error(f"Background scraping failed: {e}", exc_info=True)
            
            background_tasks.add_task(scrape_in_background)
            
            return OperationResponse(
                success=True,
                message="Scraping started in background",
                data={
                    "status": "processing",
                    "pages_per_term": request.pages_per_term,
                    "note": "Check logs or status endpoint for completion"
                }
            )
        else:
            # Run synchronously (original behavior)
            stats = run_scraping_task(
                pages=request.pages_per_term,
                search_terms=request.search_terms,
                stop_on_old_jobs=request.stop_on_old_jobs
            )
            
            return OperationResponse(
                success=True,
                message=f"Scraping completed: {stats['total_saved']} new jobs saved",
                data=stats
            )
        
    except Exception as e:
        logger.error(f"Scrape operation failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="Scraping operation failed",
            errors=[str(e)]
        )


@router.post("/process-nlp", response_model=OperationResponse)
async def run_nlp_pipeline(
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(default=False, description="Run in background mode (returns immediately)")
) -> OperationResponse:
    """
    Run NLP processing pipeline on unprocessed jobs
    
    This endpoint processes raw job descriptions to extract:
    - Skills and technologies
    - Salary information
    - Employment type
    - Experience level
    - Work arrangement (remote/hybrid/onsite)
    
    Args:
        background_tasks: FastAPI background tasks
        async_mode: If True, runs in background and returns immediately
    
    Returns:
        OperationResponse with processing statistics
        
    Example:
        POST /api/v1/operations/process-nlp?async_mode=true
    """
    try:
        logger.info(f"NLP pipeline operation requested, async={async_mode}")
        
        if async_mode:
            # Run in background
            def nlp_in_background():
                try:
                    pipeline = DataProcessingPipeline()
                    status = pipeline.get_processing_status()
                    unprocessed_count = status['raw_jobs']['unprocessed']
                    
                    if unprocessed_count > 0:
                        logger.info(f"Background NLP processing {unprocessed_count} jobs...")
                        stats = pipeline.process_unprocessed_jobs()
                        logger.info(f"Background NLP completed: {stats.processed_jobs} jobs processed")
                    else:
                        logger.info("No unprocessed jobs for NLP")
                except Exception as e:
                    logger.error(f"Background NLP failed: {e}", exc_info=True)
            
            background_tasks.add_task(nlp_in_background)
            
            return OperationResponse(
                success=True,
                message="NLP processing started in background",
                data={
                    "status": "processing",
                    "note": "Check logs or status endpoint for completion"
                }
            )
        else:
            # Run synchronously
            pipeline = DataProcessingPipeline()
            
            # Get current status
            status = pipeline.get_processing_status()
            unprocessed_count = status['raw_jobs']['unprocessed']
            
            if unprocessed_count == 0:
                return OperationResponse(
                    success=True,
                    message="No unprocessed jobs to process",
                    data={
                        "processed": 0,
                        "total": 0,
                        "tech_jobs_found": 0
                    }
                )
            
            logger.info(f"Processing {unprocessed_count} unprocessed jobs...")
            stats = pipeline.process_unprocessed_jobs()
            
            return OperationResponse(
                success=True,
                message=f"NLP processing completed: {stats.processed_jobs}/{stats.total_jobs} jobs processed",
                data={
                    "processed": stats.processed_jobs,
                    "total": stats.total_jobs,
                    "tech_jobs_found": stats.tech_jobs_found,
                    "jobs_with_salary": stats.jobs_with_salary,
                    "jobs_with_skills": stats.jobs_with_skills,
                    "avg_processing_time": round(stats.avg_processing_time, 2),
                    "errors": len(stats.errors)
                },
                errors=stats.errors[:10] if stats.errors else None
            )
        
    except Exception as e:
        logger.error(f"NLP pipeline operation failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="NLP processing operation failed",
            errors=[str(e)]
        )


@router.post("/check-urls", response_model=OperationResponse)
async def check_job_urls(
    request: URLCheckRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(default=False, description="Run in background mode (returns immediately)")
) -> OperationResponse:
    """
    Check URLs for existing jobs and mark inactive ones
    
    This endpoint checks the accessibility of job posting URLs and marks
    jobs as inactive if their URLs are no longer accessible.
    
    Args:
        request: URL checking parameters
        background_tasks: FastAPI background tasks
        async_mode: If True, runs in background and returns immediately
        
    Returns:
        OperationResponse with URL checking statistics
        
    Example:
        POST /api/v1/operations/check-urls?async_mode=true
        {
            "older_than_days": 7,
            "batch_size": 30
        }
    """
    try:
        logger.info(f"URL check operation requested: older_than_days={request.older_than_days}, async={async_mode}")
        
        if async_mode:
            # Run in background
            def url_check_in_background():
                try:
                    logger.info("Background URL checking started...")
                    db = SessionLocal()
                    url_checker = URLChecker(timeout=10, max_retries=2)
                    
                    try:
                        # Find jobs to check
                        cutoff_date = datetime.utcnow() - timedelta(days=request.older_than_days)
                        query = db.query(Job.id, Job.original_url, Job.scraped_at).filter(
                            Job.is_active == True,
                            Job.original_url.isnot(None),
                            Job.original_url != '',
                            Job.scraped_at < cutoff_date
                        ).order_by(Job.scraped_at.asc())
                        
                        if request.limit:
                            query = query.limit(request.limit)
                        
                        jobs_to_check = [(r.id, r.original_url, r.scraped_at) for r in query.all()]
                        
                        if not jobs_to_check:
                            logger.info("No jobs found to check")
                            return
                        
                        logger.info(f"Checking {len(jobs_to_check)} job URLs...")
                        
                        checked = 0
                        marked_inactive = 0
                        
                        # Process in batches
                        for i in range(0, len(jobs_to_check), request.batch_size):
                            batch = jobs_to_check[i:i + request.batch_size]
                            
                            for job_id, url, scraped_at in batch:
                                try:
                                    is_accessible, status_message, status_code = url_checker.check_url_accessibility(url)
                                    checked += 1
                                    
                                    if not is_accessible:
                                        job = db.query(Job).filter(Job.id == job_id).first()
                                        if job:
                                            job.is_active = False
                                            marked_inactive += 1
                                            logger.debug(f"Marked job {job_id} as inactive")
                                
                                except Exception as e:
                                    logger.error(f"Error checking job {job_id}: {e}")
                            
                            db.commit()
                        
                        logger.info(f"Background URL checking completed: {checked} checked, {marked_inactive} marked inactive")
                    
                    finally:
                        url_checker.close()
                        db.close()
                        
                except Exception as e:
                    logger.error(f"Background URL checking failed: {e}", exc_info=True)
            
            background_tasks.add_task(url_check_in_background)
            
            return OperationResponse(
                success=True,
                message="URL checking started in background",
                data={
                    "status": "processing",
                    "older_than_days": request.older_than_days,
                    "batch_size": request.batch_size,
                    "note": "Check logs or status endpoint for completion"
                }
            )
        
        # Synchronous mode (existing code)
        
        db = SessionLocal()
        url_checker = URLChecker(timeout=10, max_retries=2)
        
        try:
            # Find jobs to check
            cutoff_date = datetime.utcnow() - timedelta(days=request.older_than_days)
            query = db.query(Job.id, Job.original_url, Job.scraped_at).filter(
                Job.is_active == True,
                Job.original_url.isnot(None),
                Job.original_url != '',
                Job.scraped_at < cutoff_date
            ).order_by(Job.scraped_at.asc())
            
            if request.limit:
                query = query.limit(request.limit)
            
            jobs_to_check = [(r.id, r.original_url, r.scraped_at) for r in query.all()]
            
            if not jobs_to_check:
                return OperationResponse(
                    success=True,
                    message="No jobs found to check",
                    data={
                        "checked": 0,
                        "kept_active": 0,
                        "marked_inactive": 0
                    }
                )
            
            logger.info(f"Checking {len(jobs_to_check)} job URLs...")
            
            checked = 0
            kept_active = 0
            marked_inactive = 0
            errors = []
            
            # Process in batches
            for i in range(0, len(jobs_to_check), request.batch_size):
                batch = jobs_to_check[i:i + request.batch_size]
                
                for job_id, url, scraped_at in batch:
                    try:
                        is_accessible, status_message, status_code = url_checker.check_url_accessibility(url)
                        checked += 1
                        
                        if is_accessible:
                            kept_active += 1
                        else:
                            # Mark as inactive
                            job = db.query(Job).filter(Job.id == job_id).first()
                            if job:
                                job.is_active = False
                                marked_inactive += 1
                                logger.info(f"Marked job {job_id} as inactive: {status_message}")
                    
                    except Exception as e:
                        error_msg = f"Error checking job {job_id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Commit batch
                db.commit()
            
            return OperationResponse(
                success=True,
                message=f"URL checking completed: {marked_inactive} jobs marked inactive",
                data={
                    "checked": checked,
                    "kept_active": kept_active,
                    "marked_inactive": marked_inactive,
                    "errors": len(errors)
                },
                errors=errors[:10] if errors else None
            )
            
        finally:
            url_checker.close()
            db.close()
        
    except Exception as e:
        logger.error(f"URL check operation failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="URL checking operation failed",
            errors=[str(e)]
        )


@router.get("/verify-data", response_model=OperationResponse)
async def verify_data_quality(db: Session = Depends(get_db)) -> OperationResponse:
    """
    Verify data quality and completeness
    
    This endpoint performs various data quality checks including:
    - Recent scraping activity
    - Processing status
    - NLP extraction quality
    - Data distribution
    
    Returns:
        OperationResponse with data quality metrics
        
    Example:
        GET /api/v1/operations/verify-data
    """
    try:
        logger.info("Data verification requested")
        
        verification_data = {}
        
        # 1. Check recent scraping
        recent_scrapes = db.query(func.count(RawJob.id)).filter(
            RawJob.scraped_at >= datetime.now() - timedelta(hours=24)
        ).scalar()
        
        verification_data['recent_scraping'] = {
            'last_24h': recent_scrapes
        }
        
        # 2. Processing status
        total_raw = db.query(func.count(RawJob.id)).scalar()
        processed = db.query(func.count(RawJob.id)).filter(RawJob.processed == True).scalar()
        unprocessed = total_raw - processed
        
        verification_data['processing_status'] = {
            'total_raw': total_raw,
            'processed': processed,
            'unprocessed': unprocessed,
            'processed_percentage': round((processed / total_raw * 100) if total_raw > 0 else 0, 1)
        }
        
        # 3. NLP extraction quality
        total_jobs = db.query(func.count(Job.id)).scalar()
        jobs_with_skills = db.query(func.count(Job.id)).filter(Job.extracted_skills != {}).scalar()
        jobs_with_salary = db.query(func.count(Job.id)).filter(Job.salary_min.isnot(None)).scalar()
        
        if total_jobs > 0:
            verification_data['nlp_quality'] = {
                'total_jobs': total_jobs,
                'jobs_with_skills': jobs_with_skills,
                'jobs_with_salary': jobs_with_salary,
                'skills_percentage': round(jobs_with_skills / total_jobs * 100, 1),
                'salary_percentage': round(jobs_with_salary / total_jobs * 100, 1)
            }
        else:
            verification_data['nlp_quality'] = {
                'total_jobs': 0,
                'warning': 'No processed jobs found'
            }
        
        # 4. Work arrangement distribution
        work_dist = db.query(
            Job.work_arrangement,
            func.count(Job.id).label('count')
        ).group_by(Job.work_arrangement).all()
        
        verification_data['work_arrangement_distribution'] = {
            str(arrangement): count for arrangement, count in work_dist
        }
        
        # 5. Active vs inactive jobs
        active_jobs = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar()
        inactive_jobs = db.query(func.count(Job.id)).filter(Job.is_active == False).scalar()
        
        verification_data['job_status'] = {
            'active': active_jobs,
            'inactive': inactive_jobs,
            'active_percentage': round((active_jobs / (active_jobs + inactive_jobs) * 100) if (active_jobs + inactive_jobs) > 0 else 0, 1)
        }
        
        return OperationResponse(
            success=True,
            message="Data verification completed",
            data=verification_data
        )
        
    except Exception as e:
        logger.error(f"Data verification failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="Data verification failed",
            errors=[str(e)]
        )


@router.post("/daily-update", response_model=OperationResponse)
async def run_daily_update(
    pages_per_term: int = Query(default=3, ge=1, le=20),
    url_check_older_than: int = Query(default=7, ge=1)
) -> OperationResponse:
    """
    Run complete daily update operation
    
    This endpoint orchestrates the entire daily update process:
    1. Scrape new jobs
    2. Process with NLP pipeline
    3. Check URLs for older jobs
    4. Verify data quality
    
    This is the main endpoint called by automated tasks.
    
    Args:
        pages_per_term: Number of pages to scrape per search term
        url_check_older_than: Check URLs for jobs older than N days
        
    Returns:
        OperationResponse with complete update statistics
        
    Example:
        POST /api/v1/operations/daily-update?pages_per_term=3&url_check_older_than=7
    """
    try:
        logger.info("=" * 60)
        logger.info("STARTING DAILY UPDATE OPERATION")
        logger.info("=" * 60)
        
        update_stats = {
            'start_time': datetime.now().isoformat(),
            'steps': []
        }
        
        # Step 1: Scrape new jobs
        logger.info("\nStep 1: Scraping new jobs...")
        try:
            scrape_result = await run_incremental_scrape(
                ScrapeRequest(pages_per_term=pages_per_term),
                BackgroundTasks()
            )
            update_stats['steps'].append({
                'name': 'scraping',
                'success': scrape_result.success,
                'data': scrape_result.data,
                'errors': scrape_result.errors
            })
            logger.info(f"Scraping completed: {scrape_result.message}")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            update_stats['steps'].append({
                'name': 'scraping',
                'success': False,
                'errors': [str(e)]
            })
        
        # Step 2: Run NLP pipeline
        logger.info("\nStep 2: Running NLP pipeline...")
        try:
            nlp_result = await run_nlp_pipeline()
            update_stats['steps'].append({
                'name': 'nlp_processing',
                'success': nlp_result.success,
                'data': nlp_result.data,
                'errors': nlp_result.errors
            })
            logger.info(f"NLP processing completed: {nlp_result.message}")
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            update_stats['steps'].append({
                'name': 'nlp_processing',
                'success': False,
                'errors': [str(e)]
            })
        
        # Step 3: Check URLs for older jobs
        logger.info("\nStep 3: Checking URLs for older jobs...")
        try:
            url_result = await check_job_urls(
                URLCheckRequest(
                    older_than_days=url_check_older_than,
                    batch_size=30
                )
            )
            update_stats['steps'].append({
                'name': 'url_checking',
                'success': url_result.success,
                'data': url_result.data,
                'errors': url_result.errors
            })
            logger.info(f"URL checking completed: {url_result.message}")
        except Exception as e:
            logger.error(f"URL checking failed: {e}")
            update_stats['steps'].append({
                'name': 'url_checking',
                'success': False,
                'errors': [str(e)]
            })
        
        # Step 4: Verify data quality
        logger.info("\nStep 4: Verifying data quality...")
        try:
            db = SessionLocal()
            verify_result = await verify_data_quality(db)
            db.close()
            update_stats['steps'].append({
                'name': 'data_verification',
                'success': verify_result.success,
                'data': verify_result.data,
                'errors': verify_result.errors
            })
            logger.info(f"Data verification completed: {verify_result.message}")
        except Exception as e:
            logger.error(f"Data verification failed: {e}")
            update_stats['steps'].append({
                'name': 'data_verification',
                'success': False,
                'errors': [str(e)]
            })
        
        update_stats['end_time'] = datetime.now().isoformat()
        
        # Check if all steps succeeded
        all_success = all(step['success'] for step in update_stats['steps'])
        
        logger.info("\n" + "=" * 60)
        logger.info(f"DAILY UPDATE {'COMPLETED' if all_success else 'COMPLETED WITH ERRORS'}")
        logger.info("=" * 60)
        
        return OperationResponse(
            success=all_success,
            message="Daily update completed" if all_success else "Daily update completed with errors",
            data=update_stats
        )
        
    except Exception as e:
        logger.error(f"Daily update operation failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="Daily update operation failed",
            errors=[str(e)]
        )


@router.get("/status", response_model=OperationResponse)
async def get_operations_status(db: Session = Depends(get_db)) -> OperationResponse:
    """
    Get current operations status
    
    Returns quick statistics about the system status including:
    - Last scrape time
    - Unprocessed jobs count
    - Active jobs count
    - Recent processing activity
    
    Returns:
        OperationResponse with status information
        
    Example:
        GET /api/v1/operations/status
    """
    try:
        status_data = {}
        
        # Last scrape time
        last_scrape = db.query(func.max(RawJob.scraped_at)).scalar()
        status_data['last_scrape'] = last_scrape.isoformat() if last_scrape else None
        
        # Unprocessed jobs
        unprocessed = db.query(func.count(RawJob.id)).filter(RawJob.processed == False).scalar()
        status_data['unprocessed_jobs'] = unprocessed
        
        # Active jobs
        active_jobs = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar()
        status_data['active_jobs'] = active_jobs
        
        # Recent processing (last 24h)
        recent_processed = db.query(func.count(Job.id)).filter(
            Job.processed_at >= datetime.now() - timedelta(hours=24)
        ).scalar()
        status_data['processed_last_24h'] = recent_processed
        
        return OperationResponse(
            success=True,
            message="Operations status retrieved",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        return OperationResponse(
            success=False,
            message="Failed to retrieve operations status",
            errors=[str(e)]
        )

