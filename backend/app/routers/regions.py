"""
Regional insights API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import crud
from app import schemas
from app import models

router = APIRouter(prefix="/regions", tags=["regions"])

@router.get("/with-stats", response_model=schemas.PaginatedResponse)
async def get_regions_with_stats(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search regions by city or region name"),
    time_period: Optional[int] = Query(None, ge=0, description="Time period in days (30, 60, 90, or None for all time)"),
    skills: Optional[List[str]] = Query(None, description="Filter by specific skills"),
    db: Session = Depends(get_db)
):
    """
    Get regions with job statistics.
    
    - **page**: Page number (1-indexed)
    - **limit**: Maximum number of records to return per page
    - **search**: Optional search query for location name
    - **time_period**: Optional time period in days to filter jobs
    - **skills**: Optional list of skills to filter jobs
    """
    skip = (page - 1) * limit
    
    # Get locations with stats
    locations_with_stats, total_count = crud.get_locations_with_stats(
        db, skip=skip, limit=limit, search=search, time_period=time_period, skills=skills
    )
    
    # Ensure total_count is not None
    total_count = total_count or 0
    
    result = []
    for location_data in locations_with_stats:
        try:
            location = location_data[0]  # The Location object
            
            # Get top companies for this region (top 3 for overview)
            top_companies = crud.get_region_top_companies(
                db, location.id, limit=3, time_period=time_period, skills=skills
            )
            
            # Create the response object
            location_dict = {
                'id': location.id,
                'city': location.city,
                'region': location.region,
                'country': location.country,
                'created_at': location.created_at,
                'total_jobs_count': int(location_data[1]) if location_data[1] is not None else 0,
                'active_jobs_count': int(location_data[2]) if location_data[2] is not None else 0,
                'avg_salary': float(location_data[3]) if location_data[3] is not None else None,
                'top_companies': top_companies
            }
            
            location_with_stats = schemas.LocationWithStats(**location_dict)
            result.append(location_with_stats)
        except Exception as e:
            # Log the error but continue processing other locations
            print(f"Error processing location data: {e}")
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

@router.get("/{region_id}", response_model=schemas.LocationWithStats)
async def get_region(
    region_id: int,
    time_period: Optional[int] = Query(None, ge=0, description="Time period in days (30, 60, 90, or None for all time)"),
    skills: Optional[List[str]] = Query(None, description="Filter by specific skills"),
    db: Session = Depends(get_db)
):
    """
    Get a specific region by ID with detailed statistics.
    
    - **region_id**: The ID of the region to retrieve
    - **time_period**: Optional time period in days to filter jobs
    - **skills**: Optional list of skills to filter jobs
    """
    region_details = crud.get_region_details(
        db, location_id=region_id, time_period=time_period, skills=skills
    )
    
    if not region_details:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return schemas.LocationWithStats(**region_details)

@router.get("/{region_id}/companies")
async def get_region_companies(
    region_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of companies to return"),
    time_period: Optional[int] = Query(None, ge=0, description="Time period in days (30, 60, 90, or None for all time)"),
    skills: Optional[List[str]] = Query(None, description="Filter by specific skills"),
    db: Session = Depends(get_db)
):
    """
    Get top companies hiring in a specific region.
    
    - **region_id**: The ID of the region
    - **limit**: Maximum number of companies to return
    - **time_period**: Optional time period in days to filter jobs
    - **skills**: Optional list of skills to filter jobs
    """
    # Verify region exists
    location = crud.get_location(db, region_id)
    if not location:
        raise HTTPException(status_code=404, detail="Region not found")
    
    companies = crud.get_region_top_companies(
        db, location_id=region_id, limit=limit, time_period=time_period, skills=skills
    )
    
    return {
        "region_id": region_id,
        "region_name": f"{location.city}, {location.region}" if location.region else location.city,
        "companies": companies
    }

@router.get("/{region_id}/jobs", response_model=schemas.PaginatedResponse)
async def get_region_jobs(
    region_id: int,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    time_period: Optional[int] = Query(None, ge=0, description="Time period in days (30, 60, 90, or None for all time)"),
    skills: Optional[List[str]] = Query(None, description="Filter by specific skills"),
    is_active: bool = Query(True, description="Only active jobs"),
    db: Session = Depends(get_db)
):
    """
    Get all jobs in a specific region.
    
    - **region_id**: The ID of the region
    - **page**: Page number (1-indexed)
    - **limit**: Maximum number of jobs to return
    - **time_period**: Optional time period in days to filter jobs
    - **skills**: Optional list of skills to filter jobs
    - **is_active**: Include only active job postings
    """
    # Verify region exists
    location = crud.get_location(db, region_id)
    if not location:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Calculate skip for pagination
    skip = (page - 1) * limit
    
    # Build filters
    filters = schemas.JobSearchParams(
        offset=skip,
        limit=limit,
        location_id=region_id,
        is_active=is_active,
        skills=skills
    )
    
    # Apply time filter if specified
    if time_period and time_period > 0:
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=time_period)
        filters.posted_after = cutoff_date
    
    # Get jobs and count
    jobs = crud.get_jobs(db, skip=skip, limit=limit, filters=filters)
    total_count = crud.count_jobs(db, filters=filters)
    
    # Convert to response format
    job_list = [schemas.Job.from_orm(job) for job in jobs]
    
    # Calculate pagination metadata
    total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1
    
    return schemas.PaginatedResponse(
        items=job_list,
        total=total_count,
        page=page,
        pages=total_pages,
        per_page=limit,
        has_next=page < total_pages,
        has_prev=page > 1
    )

