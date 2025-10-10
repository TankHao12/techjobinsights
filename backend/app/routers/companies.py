"""
Company-related API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import crud
from app import schemas
from app import models

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/popular", response_model=List[dict])
async def get_popular_companies(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of companies to return"),
    db: Session = Depends(get_db)
):
    """
    Get popular companies for autocomplete functionality.
    Returns simplified company objects for frontend use.
    """
    companies = crud.get_companies_with_job_count(db, limit=limit)
    return [
        {
            "id": company[0].id,
            "name": company[0].name,
            "job_count": company[1] if len(company) > 1 else 0
        }
        for company in companies
    ]

@router.get("/", response_model=List[schemas.Company])
async def get_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    db: Session = Depends(get_db)
):
    """
    Get companies with optional filtering.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-500)
    - **industry**: Filter companies by industry
    """
    companies = crud.get_companies(db, skip=skip, limit=limit, industry=industry)
    return [schemas.Company.from_orm(company) for company in companies]

@router.get("/with-stats", response_model=schemas.PaginatedResponse)
async def get_companies_with_stats(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search companies by name"),
    db: Session = Depends(get_db)
):
    """
    Get companies with job statistics (active jobs, total jobs, avg salary).
    
    - **page**: Page number (1-indexed)
    - **limit**: Maximum number of records to return per page
    - **search**: Optional search query for company name
    """
    skip = (page - 1) * limit
    
    # Get filtered companies with stats
    companies_with_stats, total_count = crud.get_companies_with_stats(
        db, skip=skip, limit=limit, search=search
    )
    
    # Ensure total_count is not None
    total_count = total_count or 0
    
    result = []
    for company_data in companies_with_stats:
        try:
            company = company_data[0]  # The Company object
            
            # Create the response object with all fields at once
            # company_data structure: (Company, total_jobs_count, active_jobs_count)
            company_dict = {
                'id': company.id,
                'name': company.name,
                'normalized_name': company.normalized_name,
                'created_at': company.created_at,
                'total_jobs_count': int(company_data[1]) if company_data[1] is not None else 0,
                'active_jobs_count': int(company_data[2]) if company_data[2] is not None else 0,
            }
            
            company_with_stats = schemas.CompanyWithStats(**company_dict)
            result.append(company_with_stats)
        except Exception as e:
            # Log the error but continue processing other companies
            print(f"Error processing company data: {e}")
            continue
    
    # Calculate pagination metadata
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1
    
    return schemas.PaginatedResponse(
        items=result,
        total=total_count,
        page=page,
        pages=total_pages,
        per_page=limit,
        has_next=page < total_pages,
        has_prev=page > 1
    )

@router.get("/industries", response_model=List[str])
async def get_industries(db: Session = Depends(get_db)):
    """
    Get all unique industries from companies.
    """
    industries = db.query(models.Company.industry).distinct().filter(
        models.Company.industry.isnot(None)
    ).all()
    return [industry[0] for industry in industries if industry[0]]

@router.get("/by-tech")
async def find_companies_by_technology(
    tech: str = Query(..., description="Technology/skill name to search for"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of companies to return"),
    db: Session = Depends(get_db)
):
    """
    Find companies using a specific technology.
    Returns companies with job counts for that technology.
    
    US-3.3: Find Companies by Technology
    """
    from sqlalchemy import text
    
    query = text("""
        WITH skill_jobs AS (
            SELECT DISTINCT j.company_id, j.id as job_id
            FROM jobs j, jsonb_each(j.extracted_skills) skills
            WHERE j.extracted_skills IS NOT NULL
                AND j.is_tech_job = TRUE
                AND EXISTS (
                    SELECT 1 
                    FROM jsonb_array_elements_text(skills.value) AS skill
                    WHERE LOWER(skill) = LOWER(:tech)
                )
        )
        SELECT 
            c.id,
            c.name,
            COUNT(sj.job_id) as job_count
        FROM companies c
        INNER JOIN skill_jobs sj ON c.id = sj.company_id
        GROUP BY c.id, c.name
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"tech": tech, "limit": limit}).fetchall()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "job_count": row.job_count
        }
        for row in result
    ]

@router.get("/{company_id}", response_model=schemas.Company)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """
    Get a specific company by ID.
    
    - **company_id**: The ID of the company to retrieve
    """
    company = crud.get_company(db, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return schemas.Company.from_orm(company)

@router.get("/{company_id}/jobs", response_model=List[schemas.Job])
async def get_company_jobs(
    company_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    is_active: bool = Query(True, description="Only active jobs"),
    db: Session = Depends(get_db)
):
    """
    Get all jobs posted by a specific company.
    
    - **company_id**: The ID of the company
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of jobs to return
    - **is_active**: Include only active job postings
    """
    # Verify company exists
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Create filter for this company
    filters = schemas.JobSearchParams(
        offset=skip,
        limit=limit,
        company_id=company_id,
        is_active=is_active
    )
    
    jobs = crud.get_jobs(db, skip=skip, limit=limit, filters=filters)
    return [schemas.Job.from_orm(job) for job in jobs]

@router.post("/", response_model=schemas.Company)
async def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    """
    Create a new company.
    
    - **company**: Company data including name, website, industry, etc.
    """
    # Check if company with same name already exists
    existing_company = crud.get_company_by_name(db, company.name)
    if existing_company:
        raise HTTPException(status_code=400, detail="Company with this name already exists")
    
    return crud.create_company(db=db, company=company)

@router.get("/{company_id}/tech-stack")
async def get_company_tech_stack(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get aggregated tech stack for a company based on all their job postings.
    Returns skills grouped by category with confidence levels.
    
    US-3.2: Company Tech Stack View
    """
    from sqlalchemy import text
    from collections import defaultdict
    
    # Verify company exists
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get job count for context
    job_count_query = db.query(models.Job).filter(
        models.Job.company_id == company_id,
        models.Job.is_tech_job == True
    ).count()
    
    # Aggregate skills from all company jobs
    query = text("""
        WITH company_skills AS (
            SELECT 
                key as category,
                jsonb_array_elements_text(value) as skill,
                COUNT(*) as mention_count
            FROM jobs, jsonb_each(extracted_skills)
            WHERE company_id = :company_id 
                AND extracted_skills IS NOT NULL
                AND is_tech_job = TRUE
            GROUP BY key, jsonb_array_elements_text(value)
        )
        SELECT 
            category,
            skill,
            mention_count,
            CASE
                WHEN mention_count > 5 THEN 'high'
                WHEN mention_count BETWEEN 3 AND 5 THEN 'medium'
                ELSE 'low'
            END as confidence
        FROM company_skills
        ORDER BY category, mention_count DESC
    """)
    
    result = db.execute(query, {"company_id": company_id}).fetchall()
    
    # Group by category
    tech_stack = defaultdict(list)
    for row in result:
        tech_stack[row.category].append({
            "name": row.skill,
            "count": row.mention_count,
            "confidence": row.confidence
        })
    
    return {
        "company_id": company_id,
        "company_name": company.name,
        "job_count": job_count_query,
        "tech_stack": dict(tech_stack)
    }

@router.put("/{company_id}", response_model=schemas.Company)
async def update_company(
    company_id: int,
    company_update: schemas.CompanyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing company.
    
    - **company_id**: The ID of the company to update
    - **company_update**: Updated company data
    """
    # Check if company exists
    existing_company = crud.get_company(db, company_id)
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if new name conflicts with existing company
    if company_update.name:
        name_conflict = crud.get_company_by_name(db, company_update.name)
        if name_conflict and name_conflict.id != company_id:
            raise HTTPException(status_code=400, detail="Company with this name already exists")
    
    company = crud.update_company(db, company_id=company_id, company_update=company_update)
    return company