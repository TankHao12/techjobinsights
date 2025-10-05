"""
CRUD operations for database models
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from app import models
from app import schemas

# =============================================================================
# COMPANY CRUD OPERATIONS
# =============================================================================

def get_company(db: Session, company_id: int) -> Optional[models.Company]:
    """Get a company by ID"""
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_company_by_name(db: Session, name: str) -> Optional[models.Company]:
    """Get a company by name"""
    return db.query(models.Company).filter(models.Company.name == name).first()

def get_companies(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    industry: Optional[str] = None
) -> List[models.Company]:
    """Get companies with optional filtering"""
    query = db.query(models.Company)
    
    if industry:
        query = query.filter(models.Company.industry == industry)
    
    return query.offset(skip).limit(limit).all()

def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    """Create a new company"""
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(
    db: Session, 
    company_id: int, 
    company_update: schemas.CompanyUpdate
) -> Optional[models.Company]:
    """Update a company"""
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

def get_companies_with_stats(db: Session, skip: int = 0, limit: int = 100):
    """Get companies with job statistics"""
    return db.query(
        models.Company,
        func.count(models.Job.id).filter(models.Job.is_tech_job == True).label('total_jobs_count'),
        func.count(models.Job.id).filter(
            and_(models.Job.is_active == True, models.Job.is_tech_job == True)
        ).label('active_jobs_count'),
        func.avg(models.Job.salary_max).filter(models.Job.is_tech_job == True).label('avg_salary_offered')
    ).outerjoin(models.Job).group_by(models.Company.id).offset(skip).limit(limit).all()

def get_companies_with_job_count(db: Session, limit: int = 100):
    """Get companies ordered by job count for autocomplete"""
    return db.query(
        models.Company,
        func.count(models.Job.id).filter(models.Job.is_tech_job == True).label('job_count')
    ).outerjoin(models.Job).group_by(models.Company.id).order_by(
        desc(func.count(models.Job.id).filter(models.Job.is_tech_job == True))
    ).limit(limit).all()

# =============================================================================
# LOCATION CRUD OPERATIONS
# =============================================================================

def get_location(db: Session, location_id: int) -> Optional[models.Location]:
    """Get a location by ID"""
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def get_location_by_city(db: Session, city: str) -> Optional[models.Location]:
    """Get a location by city name"""
    return db.query(models.Location).filter(models.Location.city == city).first()

def get_locations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Location]:
    """Get all locations"""
    return db.query(models.Location).offset(skip).limit(limit).all()

def create_location(db: Session, location: schemas.LocationCreate) -> models.Location:
    """Create a new location"""
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

# =============================================================================
# CATEGORY CRUD OPERATIONS
# =============================================================================

def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Get a category by ID"""
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session) -> List[models.Category]:
    """Get all categories ordered by sort_order"""
    return db.query(models.Category).order_by(models.Category.sort_order).all()

def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    """Create a new category"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# =============================================================================
# SKILL OPERATIONS (JSONB-based)
# =============================================================================
# Note: This schema uses JSONB for skills storage, not separate tables

def get_trending_skills(
    db: Session,
    days: int = 30,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get trending skills based on recent job postings (JSONB-based)"""
    cutoff_date = date.today() - timedelta(days=days)
    
    # Use raw SQL for JSONB skill extraction
    query = text("""
        SELECT skill, COUNT(*) as job_count, AVG(salary_max) as avg_salary
        FROM (
            SELECT jsonb_array_elements_text(value) as skill, salary_max
            FROM jobs, jsonb_each(extracted_skills)
            WHERE extracted_skills IS NOT NULL 
            AND is_tech_job = TRUE
            AND is_active = TRUE
            AND posted_date >= :cutoff_date
        ) skills_data
        GROUP BY skill
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"cutoff_date": cutoff_date, "limit": limit})
    return [{
        "name": row.skill,
        "job_count": row.job_count,
        "avg_salary": float(row.avg_salary) if row.avg_salary else None
    } for row in result.fetchall()]

def get_skills_with_stats(db: Session, skip: int = 0, limit: int = 100):
    """Get skills with job statistics (JSONB-based)"""
    query = text("""
        SELECT skill, COUNT(*) as job_count, AVG(salary_max) as avg_salary
        FROM (
            SELECT jsonb_array_elements_text(value) as skill, salary_max
            FROM jobs, jsonb_each(extracted_skills)
            WHERE extracted_skills IS NOT NULL 
            AND is_tech_job = TRUE
            AND is_active = TRUE
        ) skills_data
        GROUP BY skill
        ORDER BY job_count DESC
        OFFSET :skip LIMIT :limit
    """)
    
    result = db.execute(query, {"skip": skip, "limit": limit})
    return [{
        "skill": row.skill,
        "job_count": row.job_count,
        "avg_salary": float(row.avg_salary) if row.avg_salary else None
    } for row in result.fetchall()]

def get_skills_with_job_count(db: Session, limit: int = 100):
    """Get skills ordered by job count for autocomplete (JSONB-based)"""
    query = text("""
        SELECT skill, COUNT(*) as job_count
        FROM (
            SELECT jsonb_array_elements_text(value) as skill
            FROM jobs, jsonb_each(extracted_skills)
            WHERE extracted_skills IS NOT NULL 
            AND is_tech_job = TRUE
            AND is_active = TRUE
        ) skills_data
        GROUP BY skill
        ORDER BY job_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    return [{
        "skill": row.skill,
        "job_count": row.job_count
    } for row in result.fetchall()]

# =============================================================================
# JOB CRUD OPERATIONS
# =============================================================================

def get_job(db: Session, job_id: int) -> Optional[models.Job]:
    """Get a job by ID with related data"""
    return db.query(models.Job).options(
        joinedload(models.Job.company),
        joinedload(models.Job.location),
        joinedload(models.Job.category),
        joinedload(models.Job.job_skills).joinedload(models.JobSkill.skill)
    ).filter(
        and_(
            models.Job.id == job_id,
            models.Job.is_tech_job == True  # BUSINESS LOGIC: Only show tech jobs
        )
    ).first()

def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[schemas.JobSearchParams] = None
) -> List[models.Job]:
    """Get jobs with advanced filtering for analytics platform"""
    query = db.query(models.Job).options(
        joinedload(models.Job.company),
        joinedload(models.Job.location),
        joinedload(models.Job.category)
    )
    
    # BUSINESS LOGIC: Only show tech jobs to users
    query = query.filter(models.Job.is_tech_job == True)

    if filters:
        # Full-text search in title and description
        if filters.query:
            search_terms = filters.query.split()
            for term in search_terms:
                query = query.filter(
                    or_(
                        models.Job.title.ilike(f"%{term}%"),
                        models.Job.description.ilike(f"%{term}%"),
                    )
                )

        # Company filters
        if filters.companies:
            company_names = [name.strip() for name in filters.companies]
            query = query.join(models.Company).filter(
                models.Company.name.in_(company_names)
            )

        if filters.exclude_companies:
            exclude_company_names = [name.strip() for name in filters.exclude_companies]
            query = query.join(models.Company).filter(
                ~models.Company.name.in_(exclude_company_names)
            )

        # Legacy company_id support
        if filters.company_id:
            query = query.filter(models.Job.company_id == filters.company_id)

        # Location filters
        if filters.location:
            query = query.outerjoin(models.Location).filter(
                or_(
                    models.Location.city.ilike(f"%{filters.location}%"),
                    models.Location.region.ilike(f"%{filters.location}%"),
                    models.Job.description.ilike(f"%location%{filters.location}%")
                )
            )

        if filters.location_id:
            query = query.filter(models.Job.location_id == filters.location_id)

        # Remote work type filter
        if filters.remote_type:
            if filters.remote_type.lower() == 'remote':
                query = query.filter(
                    or_(
                        models.Job.title.ilike('%remote%'),
                        models.Job.description.ilike('%remote%'),
                        models.Job.is_remote == True
                    )
                )
            elif filters.remote_type.lower() == 'onsite':
                query = query.filter(
                    and_(
                        ~models.Job.title.ilike('%remote%'),
                        ~models.Job.description.ilike('%remote%'),
                        or_(models.Job.is_remote == False, models.Job.is_remote == None)
                    )
                )
            elif filters.remote_type.lower() == 'hybrid':
                query = query.filter(
                    or_(
                        models.Job.title.ilike('%hybrid%'),
                        models.Job.description.ilike('%hybrid%')
                    )
                )

        # Category and job type filters
        if filters.category_id:
            query = query.filter(models.Job.category_id == filters.category_id)

        if filters.employment_type:
            query = query.filter(models.Job.employment_type == filters.employment_type)

        if filters.experience_level:
            query = query.filter(models.Job.experience_level == filters.experience_level)

        # Salary filters
        if filters.salary_min:
            query = query.filter(
                or_(
                    models.Job.salary_max >= filters.salary_min,
                    models.Job.salary_min >= filters.salary_min
                )
            )

        if filters.salary_max:
            query = query.filter(
                or_(
                    models.Job.salary_min <= filters.salary_max,
                    models.Job.salary_max <= filters.salary_max
                )
            )

        # Date filters
        if filters.posted_after:
            query = query.filter(models.Job.posted_date >= filters.posted_after)

        # Active status filter
        if filters.is_active is not None:
            query = query.filter(models.Job.is_active == filters.is_active)

        # Skills filters - using JSONB queries for extracted_skills
        if filters.skills:
            for skill in filters.skills:
                query = query.filter(
                    text("extracted_skills::text ILIKE :skill")
                ).params(skill=f"%{skill}%")

        # Exclude skills - exclude jobs that have these skills
        if filters.exclude_skills:
            for skill in filters.exclude_skills:
                query = query.filter(
                    ~text("extracted_skills::text ILIKE :skill")
                ).params(skill=f"%{skill}%")

    # Order by most recent first
    query = query.order_by(desc(models.Job.scraped_at))

    # Apply pagination
    return query.offset(skip).limit(limit).all()

def count_jobs(db: Session, filters: Optional[schemas.JobSearchParams] = None) -> int:
    """Count jobs with advanced filtering for analytics platform"""
    query = db.query(models.Job)
    
    # BUSINESS LOGIC: Only count tech jobs
    query = query.filter(models.Job.is_tech_job == True)

    if filters:
        # Apply the same filters as get_jobs function
        if filters.query:
            search_terms = filters.query.split()
            for term in search_terms:
                query = query.filter(
                    or_(
                        models.Job.title.ilike(f"%{term}%"),
                        models.Job.description.ilike(f"%{term}%"),
                    )
                )

        if filters.companies:
            company_names = [name.strip() for name in filters.companies]
            query = query.join(models.Company).filter(
                models.Company.name.in_(company_names)
            )

        if filters.exclude_companies:
            exclude_company_names = [name.strip() for name in filters.exclude_companies]
            query = query.join(models.Company).filter(
                ~models.Company.name.in_(exclude_company_names)
            )

        if filters.company_id:
            query = query.filter(models.Job.company_id == filters.company_id)

        if filters.location:
            query = query.outerjoin(models.Location).filter(
                or_(
                    models.Location.city.ilike(f"%{filters.location}%"),
                    models.Location.region.ilike(f"%{filters.location}%"),
                    models.Job.description.ilike(f"%location%{filters.location}%")
                )
            )

        if filters.location_id:
            query = query.filter(models.Job.location_id == filters.location_id)

        if filters.remote_type:
            if filters.remote_type.lower() == 'remote':
                query = query.filter(
                    or_(
                        models.Job.title.ilike('%remote%'),
                        models.Job.description.ilike('%remote%'),
                        models.Job.is_remote == True
                    )
                )
            elif filters.remote_type.lower() == 'onsite':
                query = query.filter(
                    and_(
                        ~models.Job.title.ilike('%remote%'),
                        ~models.Job.description.ilike('%remote%'),
                        or_(models.Job.is_remote == False, models.Job.is_remote == None)
                    )
                )
            elif filters.remote_type.lower() == 'hybrid':
                query = query.filter(
                    or_(
                        models.Job.title.ilike('%hybrid%'),
                        models.Job.description.ilike('%hybrid%')
                    )
                )

        if filters.category_id:
            query = query.filter(models.Job.category_id == filters.category_id)

        if filters.employment_type:
            query = query.filter(models.Job.employment_type == filters.employment_type)

        if filters.experience_level:
            query = query.filter(models.Job.experience_level == filters.experience_level)

        if filters.salary_min:
            query = query.filter(
                or_(
                    models.Job.salary_max >= filters.salary_min,
                    models.Job.salary_min >= filters.salary_min
                )
            )

        if filters.salary_max:
            query = query.filter(
                or_(
                    models.Job.salary_min <= filters.salary_max,
                    models.Job.salary_max <= filters.salary_max
                )
            )

        if filters.posted_after:
            query = query.filter(models.Job.posted_date >= filters.posted_after)

        if filters.is_active is not None:
            query = query.filter(models.Job.is_active == filters.is_active)

        # Skills filters - using JSONB queries for extracted_skills
        if filters.skills:
            for skill in filters.skills:
                query = query.filter(
                    text("extracted_skills::text ILIKE :skill")
                ).params(skill=f"%{skill}%")

        if filters.exclude_skills:
            for skill in filters.exclude_skills:
                query = query.filter(
                    ~text("extracted_skills::text ILIKE :skill")
                ).params(skill=f"%{skill}%")

    return query.count()

def create_job(db: Session, job: schemas.JobCreate) -> models.Job:
    """Create a new job"""
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(
    db: Session,
    job_id: int,
    job_update: schemas.JobUpdate
) -> Optional[models.Job]:
    """Update a job"""
    db_job = get_job(db, job_id)
    if not db_job:
        return None
    
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job

def get_recent_jobs(db: Session, days: int = 7, limit: int = 50) -> List[models.Job]:
    """Get recently posted jobs"""
    cutoff_date = date.today() - timedelta(days=days)
    
    return db.query(models.Job).options(
        joinedload(models.Job.company),
        joinedload(models.Job.location)
    ).filter(
        and_(
            models.Job.posted_date >= cutoff_date,
            models.Job.is_active == True,
            models.Job.is_tech_job == True  # BUSINESS LOGIC: Only show tech jobs
        )
    ).order_by(desc(models.Job.posted_date)).limit(limit).all()

# =============================================================================
# JOB SKILL OPERATIONS (JSONB-based)
# =============================================================================
# Note: Skills are stored in JSONB format in the jobs table, not separate relationships

# =============================================================================
# ANALYTICS CRUD OPERATIONS
# =============================================================================

def get_dashboard_stats(db: Session, days: int = 0) -> Dict[str, Any]:
    """
    Get dashboard statistics
    
    Args:
        days: Time period in days (0 for all time). Filters by job posted_date.
    """
    today = date.today()
    cutoff_date = None
    if days > 0:
        cutoff_date = today - timedelta(days=days)
    
    # BUSINESS LOGIC: Only count tech jobs in dashboard stats
    # Filter by posted_date if days parameter is provided
    job_query = db.query(models.Job).filter(models.Job.is_tech_job == True)
    if cutoff_date:
        job_query = job_query.filter(models.Job.posted_date >= cutoff_date)
    
    total_jobs = job_query.count()
    
    active_jobs_query = db.query(models.Job).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    )
    if cutoff_date:
        active_jobs_query = active_jobs_query.filter(models.Job.posted_date >= cutoff_date)
    
    active_jobs = active_jobs_query.count()
    
    total_companies = db.query(models.Company).count()
    
    hiring_companies_query = db.query(models.Company).join(models.Job).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    )
    if cutoff_date:
        hiring_companies_query = hiring_companies_query.filter(models.Job.posted_date >= cutoff_date)
    
    hiring_companies = hiring_companies_query.distinct().count()
    
    # Note: Skills are stored in JSONB, no separate skills table
    total_skills = 0  # Could calculate from JSONB if needed
    
    new_jobs_today_query = db.query(models.Job).filter(
        and_(models.Job.posted_date == today, models.Job.is_tech_job == True)
    )
    new_jobs_today = new_jobs_today_query.count()
    
    avg_salary_query = db.query(func.avg(models.Job.salary_max)).filter(
        and_(
            models.Job.salary_max.isnot(None),
            models.Job.is_active == True,
            models.Job.is_tech_job == True
        )
    )
    if cutoff_date:
        avg_salary_query = avg_salary_query.filter(models.Job.posted_date >= cutoff_date)
    
    avg_salary_result = avg_salary_query.scalar()
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_companies": total_companies,
        "hiring_companies": hiring_companies,
        "total_skills": total_skills,
        "new_jobs_today": new_jobs_today,
        "avg_salary": float(avg_salary_result) if avg_salary_result else None,
        "last_updated": datetime.utcnow()
    }

def get_skill_trends(
    db: Session,
    skill_name: Optional[str] = None,
    days: int = 30,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get skill trends from SkillTrend table"""
    cutoff_date = date.today() - timedelta(days=days)
    
    query = db.query(models.SkillTrend).filter(
        models.SkillTrend.date_recorded >= cutoff_date
    )
    
    # Note: skill_id filtering removed since we don't have skills table
    # Could add skill name filtering if needed
    
    trends = query.order_by(
        desc(models.SkillTrend.date_recorded),
        desc(models.SkillTrend.demand_score)
    ).limit(limit).all()
    
    return [{
        "id": trend.id,
        "skill_id": trend.skill_id,
        "date_recorded": trend.date_recorded,
        "job_count": trend.job_count,
        "demand_score": float(trend.demand_score) if trend.demand_score else None
    } for trend in trends]

def create_skill_trend(db: Session, skill_trend_data: Dict[str, Any]) -> models.SkillTrend:
    """Create a skill trend record"""
    db_trend = models.SkillTrend(**skill_trend_data)
    db.add(db_trend)
    db.commit()
    db.refresh(db_trend)
    return db_trend

# =============================================================================
# SEARCH OPERATIONS
# =============================================================================

def search_jobs_full_text(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 100
) -> List[models.Job]:
    """Full-text search for jobs"""
    search_query = text(
        """
        SELECT j.* FROM jobs j
        WHERE to_tsvector('english', j.title || ' ' || COALESCE(j.description, '')) 
              @@ plainto_tsquery('english', :query)
        AND j.is_active = true
        AND j.is_tech_job = true
        ORDER BY ts_rank(
            to_tsvector('english', j.title || ' ' || COALESCE(j.description, '')),
            plainto_tsquery('english', :query)
        ) DESC
        OFFSET :skip LIMIT :limit
        """
    )
    
    result = db.execute(search_query, {"query": query, "skip": skip, "limit": limit})
    job_ids = [row[0] for row in result.fetchall()]
    
    if not job_ids:
        return []
    
    return db.query(models.Job).options(
        joinedload(models.Job.company),
        joinedload(models.Job.location),
        joinedload(models.Job.category)
    ).filter(models.Job.id.in_(job_ids)).all()

def search_skills_similarity(
    db: Session,
    query: str,
    threshold: float = 0.3,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search skills using JSONB data and similarity"""
    # Search within JSONB skills data
    search_query = text("""
        SELECT skill, COUNT(*) as job_count
        FROM (
            SELECT jsonb_array_elements_text(value) as skill
            FROM jobs, jsonb_each(extracted_skills)
            WHERE extracted_skills IS NOT NULL 
            AND is_tech_job = TRUE
            AND is_active = TRUE
        ) skills_data
        WHERE similarity(skill, :query) > :threshold
        GROUP BY skill
        ORDER BY similarity(skill, :query) DESC, job_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(search_query, {
        "query": query, 
        "threshold": threshold, 
        "limit": limit
    })
    return [{
        "skill": row.skill,
        "job_count": row.job_count,
        "similarity": "calculated"
    } for row in result.fetchall()]