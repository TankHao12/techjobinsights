"""
Categories API Router

Provides read-only endpoints for retrieving job categories and statistics.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db
from .. import models, schemas, crud
from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[schemas.Category])
async def get_categories(
    include_empty: bool = Query(False, description="Include categories with no jobs"),
    db: Session = Depends(get_db)
):
    """
    Get all categories ordered by sort_order.
    
    Args:
        include_empty: If True, include categories with 0 jobs
        db: Database session
        
    Returns:
        List of categories with metadata
    """
    try:
        categories = crud.get_categories(db)
        
        if not include_empty:
            # Filter out categories with no jobs
            categories_with_jobs = []
            for cat in categories:
                job_count = db.query(func.count(models.Job.id)).filter(
                    and_(models.Job.category_id == cat.id, models.Job.is_tech_job == True)
                ).scalar()
                if job_count > 0:
                    categories_with_jobs.append(cat)
            categories = categories_with_jobs
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.get("/{category_id}", response_model=schemas.Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    
    Args:
        category_id: Category ID
        db: Database session
        
    Returns:
        Category details
    """
    category = crud.get_category(db, category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.get("/{category_id}/stats")
async def get_category_stats(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific category.
    
    Args:
        category_id: Category ID
        db: Database session
        
    Returns:
        Category statistics including job count, salary ranges, etc.
    """
    category = crud.get_category(db, category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get job count - BUSINESS LOGIC: Only count tech jobs
    job_count = db.query(func.count(models.Job.id)).filter(
        and_(models.Job.category_id == category_id, models.Job.is_tech_job == True)
    ).scalar()
    
    # Get salary statistics - BUSINESS LOGIC: Only include tech jobs
    salary_stats = db.query(
        func.avg(models.Job.salary_min).label('avg_salary_min'),
        func.avg(models.Job.salary_max).label('avg_salary_max'),
        func.min(models.Job.salary_min).label('min_salary'),
        func.max(models.Job.salary_max).label('max_salary')
    ).filter(
        models.Job.category_id == category_id,
        models.Job.salary_min.isnot(None),
        models.Job.is_tech_job == True
    ).first()
    
    # Get top companies in this category - BUSINESS LOGIC: Only include tech jobs
    top_companies = db.query(
        models.Company.name,
        func.count(models.Job.id).label('job_count')
    ).join(
        models.Job, models.Job.company_id == models.Company.id
    ).filter(
        and_(models.Job.category_id == category_id, models.Job.is_tech_job == True)
    ).group_by(
        models.Company.name
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(5).all()
    
    # Get top locations - BUSINESS LOGIC: Only include tech jobs
    top_locations = db.query(
        models.Location.city,
        func.count(models.Job.id).label('job_count')
    ).join(
        models.Job, models.Job.location_id == models.Location.id
    ).filter(
        and_(models.Job.category_id == category_id, models.Job.is_tech_job == True)
    ).group_by(
        models.Location.city
    ).order_by(
        func.count(models.Job.id).desc()
    ).limit(5).all()
    
    return {
        "category": {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "color_code": category.color_code
        },
        "job_count": job_count,
        "salary_stats": {
            "avg_min": float(salary_stats.avg_salary_min) if salary_stats.avg_salary_min else None,
            "avg_max": float(salary_stats.avg_salary_max) if salary_stats.avg_salary_max else None,
            "min": float(salary_stats.min_salary) if salary_stats.min_salary else None,
            "max": float(salary_stats.max_salary) if salary_stats.max_salary else None,
        },
        "top_companies": [
            {"name": name, "job_count": count} for name, count in top_companies
        ],
        "top_locations": [
            {"city": city, "job_count": count} for city, count in top_locations
        ]
    }


@router.get("/{category_id}/jobs", response_model=schemas.PaginatedResponse)
async def get_category_jobs(
    category_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get jobs in a specific category.
    
    Args:
        category_id: Category ID
        offset: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        Paginated list of jobs in the category
    """
    category = crud.get_category(db, category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get total count - BUSINESS LOGIC: Only count tech jobs
    total = db.query(func.count(models.Job.id)).filter(
        and_(models.Job.category_id == category_id, models.Job.is_tech_job == True)
    ).scalar()
    
    # Get jobs - BUSINESS LOGIC: Only show tech jobs
    jobs = db.query(models.Job).filter(
        and_(models.Job.category_id == category_id, models.Job.is_tech_job == True)
    ).order_by(
        models.Job.posted_date.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "items": jobs,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_next": (offset + limit) < total,
        "has_prev": offset > 0
    }

