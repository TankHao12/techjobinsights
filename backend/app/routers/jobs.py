"""
Job-related API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import crud
from app import schemas
from app import models

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/", response_model=schemas.PaginatedResponse)
async def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    query: Optional[str] = Query(None, description="Search query for title/description"),
    company_id: Optional[int] = Query(None, description="Filter by company ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skills: Optional[str] = Query(None, description="Required skills (comma-separated)"),
    exclude_skills: Optional[str] = Query(None, description="Skills to exclude (comma-separated)"),
    companies: Optional[str] = Query(None, description="Include companies (comma-separated)"),
    exclude_companies: Optional[str] = Query(None, description="Exclude companies (comma-separated)"),
    employment_type: Optional[models.EmploymentType] = Query(None, description="Employment type"),
    experience_level: Optional[models.ExperienceLevel] = Query(None, description="Experience level"),
    salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
    location: Optional[str] = Query(None, description="Location filter"),
    remote_type: Optional[str] = Query(None, description="Remote work type"),
    is_active: Optional[bool] = Query(True, description="Only active jobs"),
    db: Session = Depends(get_db)
):
    """
    Get jobs with optional filtering and pagination.

    - **page**: Page number (1-based)
    - **limit**: Items per page (1-100)
    - **query**: Search in job title and description
    - **company_id**: Filter jobs by specific company
    - **location_id**: Filter jobs by location
    - **category_id**: Filter jobs by job category
    - **skills**: Required skills (comma-separated)
    - **exclude_skills**: Skills to exclude (comma-separated)
    - **companies**: Include specific companies (comma-separated)
    - **exclude_companies**: Exclude companies (comma-separated)
    - **employment_type**: Filter by employment type
    - **experience_level**: Filter by experience level
    - **salary_min**: Minimum salary filter
    - **salary_max**: Maximum salary filter
    - **location**: Location filter
    - **remote_type**: Remote work type filter
    - **is_active**: Include only active job postings
    """
    # Convert page-based to offset-based pagination
    skip = (page - 1) * limit

    # Parse comma-separated strings into lists
    skills_list = skills.split(',') if skills else None
    exclude_skills_list = exclude_skills.split(',') if exclude_skills else None
    companies_list = companies.split(',') if companies else None
    exclude_companies_list = exclude_companies.split(',') if exclude_companies else None

    filters = schemas.JobSearchParams(
        offset=skip,
        limit=limit,
        query=query,
        company_id=company_id,
        location_id=location_id,
        category_id=category_id,
        skills=skills_list,
        exclude_skills=exclude_skills_list,
        companies=companies_list,
        exclude_companies=exclude_companies_list,
        employment_type=employment_type,
        experience_level=experience_level,
        salary_min=salary_min,
        salary_max=salary_max,
        location=location,
        remote_type=remote_type,
        is_active=is_active
    )

    jobs = crud.get_jobs(db, skip=skip, limit=limit, filters=filters)
    total = crud.count_jobs(db, filters=filters)

    pages = (total + limit - 1) // limit  # Calculate total pages

    return schemas.PaginatedResponse(
        items=[schemas.Job.from_orm(job) for job in jobs],
        total=total,
        page=page,
        pages=pages,
        per_page=limit,
        has_next=page < pages,
        has_prev=page > 1
    )

@router.get("/recent", response_model=List[schemas.Job])
async def get_recent_jobs(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    db: Session = Depends(get_db)
):
    """
    Get recently posted jobs.
    
    - **days**: Number of days to look back (1-30)
    - **limit**: Maximum number of jobs to return
    """
    jobs = crud.get_recent_jobs(db, days=days, limit=limit)
    return [schemas.Job.from_orm(job) for job in jobs]

@router.get("/search", response_model=List[schemas.Job])
async def search_jobs_full_text(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Full-text search for jobs using PostgreSQL's text search capabilities.
    
    - **q**: Search query (minimum 2 characters)
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    jobs = crud.search_jobs_full_text(db, query=q, skip=skip, limit=limit)
    return [schemas.Job.from_orm(job) for job in jobs]

@router.get("/{job_id}", response_model=schemas.JobDetail)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a specific job by ID with all related information.
    
    - **job_id**: The ID of the job to retrieve
    """
    job = crud.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert to detailed response with related data
    job_detail = schemas.JobDetail.from_orm(job)
    return job_detail

@router.post("/", response_model=schemas.Job)
async def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    """
    Create a new job posting.
    
    - **job**: Job data including company_id, title, description, etc.
    """
    # Verify company exists
    company = crud.get_company(db, job.company_id)
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    # Verify location exists if provided
    if job.location_id:
        location = crud.get_location(db, job.location_id)
        if not location:
            raise HTTPException(status_code=400, detail="Location not found")
    
    # Verify category exists if provided
    if job.category_id:
        category = crud.get_category(db, job.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    return crud.create_job(db=db, job=job)

@router.put("/{job_id}", response_model=schemas.Job)
async def update_job(
    job_id: int, 
    job_update: schemas.JobUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing job posting.
    
    - **job_id**: The ID of the job to update
    - **job_update**: Updated job data
    """
    job = crud.update_job(db, job_id=job_id, job_update=job_update)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/skills")
async def get_job_skills(job_id: int, db: Session = Depends(get_db)):
    """
    Get all skills for a specific job (from JSONB field).
    
    - **job_id**: The ID of the job
    """
    # Verify job exists and get skills from JSONB
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "skills": job.extracted_skills or {},
        "message": "Skills are stored in JSONB format"
    }