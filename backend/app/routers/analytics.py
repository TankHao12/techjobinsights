"""
Analytics and dashboard API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta

from app.database import get_db
from app import crud
from app import schemas
from app import models
from app.utils.cache import cached_query

router = APIRouter(prefix="/analytics", tags=["analytics"])

# ============================================================================
# CACHED HELPER FUNCTIONS FOR ANALYTICS
# ============================================================================

@cached_query(ttl=600)  # Cache for 10 minutes
def _get_popular_skills_cached(category: Optional[str], limit: int) -> List[dict]:
    """
    Internal cached function for popular skills query.
    Separated from endpoint to enable caching with TTL.
    """
    from sqlalchemy import text
    from app.database import SessionLocal
    from app.processors.nlp_engine import NLPEngine
    
    db = SessionLocal()
    nlp_engine = NLPEngine()
    
    try:
        if category:
            # Get skills from specific category - count UNIQUE jobs per skill
            query = text("""
                WITH total_jobs AS (
                    SELECT COUNT(DISTINCT id) as total
                    FROM jobs
                    WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                )
                SELECT skill, 
                       COUNT(DISTINCT job_id) as job_count,
                       ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                FROM (
                    SELECT id as job_id, jsonb_array_elements_text(extracted_skills->:category) as skill
                    FROM jobs 
                    WHERE extracted_skills ? :category AND is_tech_job = TRUE
                ) skills_data
                GROUP BY skill
                ORDER BY job_count DESC
                LIMIT :limit
            """)
            result = db.execute(query, {"category": category, "limit": limit}).fetchall()
        else:
            # Get all skills across all categories - count UNIQUE jobs per skill
            query = text("""
                WITH total_jobs AS (
                    SELECT COUNT(DISTINCT id) as total
                    FROM jobs
                    WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                )
                SELECT skill, 
                       COUNT(DISTINCT job_id) as job_count,
                       ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                FROM (
                    SELECT id as job_id, jsonb_array_elements_text(value) as skill
                    FROM jobs, jsonb_each(extracted_skills)
                    WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                ) skills_data
                GROUP BY skill
                ORDER BY job_count DESC
                LIMIT :limit
            """)
            result = db.execute(query, {"limit": limit}).fetchall()
        
        return [
            {
                "name": row.skill,
                "display_name": nlp_engine.get_display_name(row.skill),
                "category": nlp_engine.get_skill_category(row.skill),
                "job_count": row.job_count,
                "job_percentage": float(row.job_percentage)
            }
            for row in result
        ]
    finally:
        db.close()


# ============================================================================
# SKILLS ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/skills/popular")
async def get_popular_skills(
    category: Optional[str] = Query(None, description="Skill category filter (programming_languages, web_frameworks, etc.)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of skills to return"),
    days: int = Query(0, ge=0, le=365, description="Time period in days (0 for all time)"),
    db: Session = Depends(get_db)
):
    """
    Get most popular skills across all jobs with percentages.
    
    Filters by job posted date (not scrape date).
    
    Args:
        category: Optional skill category filter
        limit: Maximum number of skills to return
        days: Time period in days (0 for all time)
        
    Returns:
        List of skills with job counts, percentages, and display names
    """
    from sqlalchemy import text
    from app.processors.nlp_engine import NLPEngine
    from fastapi import HTTPException
    from app.core.logging import get_logger
    
    nlp_engine = NLPEngine()
    logger = get_logger(__name__)
    
    try:
        # Calculate cutoff date
        cutoff_date = None
        if days > 0:
            cutoff_date = date.today() - timedelta(days=days)
        
        if category:
            # Get skills from specific category with date filtering
            if cutoff_date:
                query = text("""
                    WITH total_jobs AS (
                        SELECT COUNT(DISTINCT id) as total
                        FROM jobs
                        WHERE extracted_skills IS NOT NULL 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    )
                    SELECT skill, 
                           COUNT(DISTINCT job_id) as job_count,
                           ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                    FROM (
                        SELECT id as job_id, jsonb_array_elements_text(extracted_skills->:category) as skill
                        FROM jobs 
                        WHERE extracted_skills ? :category 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    ) skills_data
                    GROUP BY skill
                    ORDER BY job_count DESC
                    LIMIT :limit
                """)
                result = db.execute(query, {"category": category, "limit": limit, "cutoff_date": cutoff_date}).fetchall()
            else:
                query = text("""
                    WITH total_jobs AS (
                        SELECT COUNT(DISTINCT id) as total
                        FROM jobs
                        WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                    )
                    SELECT skill, 
                           COUNT(DISTINCT job_id) as job_count,
                           ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                    FROM (
                        SELECT id as job_id, jsonb_array_elements_text(extracted_skills->:category) as skill
                        FROM jobs 
                        WHERE extracted_skills ? :category AND is_tech_job = TRUE
                    ) skills_data
                    GROUP BY skill
                    ORDER BY job_count DESC
                    LIMIT :limit
                """)
                result = db.execute(query, {"category": category, "limit": limit}).fetchall()
        else:
            # Get all skills across all categories with date filtering
            if cutoff_date:
                query = text("""
                    WITH total_jobs AS (
                        SELECT COUNT(DISTINCT id) as total
                        FROM jobs
                        WHERE extracted_skills IS NOT NULL 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    )
                    SELECT skill, 
                           COUNT(DISTINCT job_id) as job_count,
                           ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                    FROM (
                        SELECT id as job_id, jsonb_array_elements_text(value) as skill
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    ) skills_data
                    GROUP BY skill
                    ORDER BY job_count DESC
                    LIMIT :limit
                """)
                result = db.execute(query, {"limit": limit, "cutoff_date": cutoff_date}).fetchall()
            else:
                query = text("""
                    WITH total_jobs AS (
                        SELECT COUNT(DISTINCT id) as total
                        FROM jobs
                        WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                    )
                    SELECT skill, 
                           COUNT(DISTINCT job_id) as job_count,
                           ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage
                    FROM (
                        SELECT id as job_id, jsonb_array_elements_text(value) as skill
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                    ) skills_data
                    GROUP BY skill
                    ORDER BY job_count DESC
                    LIMIT :limit
                """)
                result = db.execute(query, {"limit": limit}).fetchall()
        
        return [
            {
                "name": row.skill,
                "display_name": nlp_engine.get_display_name(row.skill),
                "category": nlp_engine.get_skill_category(row.skill),
                "job_count": row.job_count,
                "job_percentage": float(row.job_percentage)
            }
            for row in result
        ]
        
    except Exception as e:
        logger.error(f"Error fetching popular skills: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch popular skills")

@router.get("/skills/by-category")
async def get_skills_by_category(
    limit_per_category: int = Query(10, ge=1, le=50, description="Max skills per category"),
    days: int = Query(0, ge=0, le=365, description="Time period in days (0 for all time)"),
    db: Session = Depends(get_db)
):
    """
    Get skill distribution organized by category.
    
    Filters by job posted date (not scrape date).
    
    Args:
        limit_per_category: Max skills per category
        days: Time period in days (0 for all time)
    
    Returns:
        Skills grouped by category with job counts, percentages, and display names
    """
    from sqlalchemy import text
    from app.processors.nlp_engine import NLPEngine
    
    # Initialize NLP engine for display name mapping
    nlp_engine = NLPEngine()
    
    try:
        # Calculate cutoff date
        cutoff_date = None
        if days > 0:
            cutoff_date = date.today() - timedelta(days=days)
        
        # Count UNIQUE jobs per skill within each category
        # IMPORTANT: category_percentage shows what % of jobs IN THIS CATEGORY have this skill
        # One job can have multiple skills in the same category, but we count that job only ONCE per category
        if cutoff_date:
            query = text("""
                WITH total_jobs AS (
                    SELECT COUNT(DISTINCT id) as total
                    FROM jobs
                    WHERE extracted_skills IS NOT NULL 
                      AND is_tech_job = TRUE
                      AND posted_date >= :cutoff_date
                ),
                skill_counts AS (
                    -- Count unique jobs per skill per category
                    SELECT 
                        s.category, 
                        s.skill,
                        COUNT(DISTINCT s.job_id) as job_count
                    FROM (
                        SELECT key as category, id as job_id, jsonb_array_elements_text(value) as skill
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    ) s
                    GROUP BY s.category, s.skill
                ),
                category_totals AS (
                    -- Count UNIQUE jobs that have ANY skill in each category
                    -- This ensures percentages add up to 100% (or more if jobs have multiple skills)
                    SELECT 
                        category,
                        COUNT(DISTINCT job_id) as total_jobs_in_category
                    FROM (
                        SELECT key as category, id as job_id
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL 
                          AND is_tech_job = TRUE
                          AND posted_date >= :cutoff_date
                    ) cat_jobs
                    GROUP BY category
                )
                SELECT 
                    sc.category, 
                    sc.skill, 
                    sc.job_count,
                    ROUND(sc.job_count * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage,
                    ROUND(sc.job_count * 100.0 / ct.total_jobs_in_category, 2) as category_percentage
                FROM skill_counts sc
                JOIN category_totals ct ON sc.category = ct.category
                ORDER BY sc.category, sc.job_count DESC
            """)
            result = db.execute(query, {"cutoff_date": cutoff_date}).fetchall()
        else:
            query = text("""
                WITH total_jobs AS (
                    SELECT COUNT(DISTINCT id) as total
                    FROM jobs
                    WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                ),
                skill_counts AS (
                    -- Count unique jobs per skill per category
                    SELECT 
                        s.category, 
                        s.skill,
                        COUNT(DISTINCT s.job_id) as job_count
                    FROM (
                        SELECT key as category, id as job_id, jsonb_array_elements_text(value) as skill
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                    ) s
                    GROUP BY s.category, s.skill
                ),
                category_totals AS (
                    -- Count UNIQUE jobs that have ANY skill in each category
                    -- This ensures percentages add up to 100% (or more if jobs have multiple skills)
                    SELECT 
                        category,
                        COUNT(DISTINCT job_id) as total_jobs_in_category
                    FROM (
                        SELECT key as category, id as job_id
                        FROM jobs, jsonb_each(extracted_skills)
                        WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                    ) cat_jobs
                    GROUP BY category
                )
                SELECT 
                    sc.category, 
                    sc.skill, 
                    sc.job_count,
                    ROUND(sc.job_count * 100.0 / (SELECT total FROM total_jobs), 2) as job_percentage,
                    ROUND(sc.job_count * 100.0 / ct.total_jobs_in_category, 2) as category_percentage
                FROM skill_counts sc
                JOIN category_totals ct ON sc.category = ct.category
                ORDER BY sc.category, sc.job_count DESC
            """)
            result = db.execute(query).fetchall()
        
        # Group by category and limit per category
        categories = {}
        for row in result:
            if row.category not in categories:
                categories[row.category] = []
            if len(categories[row.category]) < limit_per_category:
                categories[row.category].append({
                    "name": row.skill,
                    "display_name": nlp_engine.get_display_name(row.skill),
                    "job_count": row.job_count,
                    "job_percentage": float(row.job_percentage),
                    "category_percentage": float(row.category_percentage)
                })
        
        return categories
        
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error fetching skills by category: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to fetch skills by category")

@router.get("/skills/by-job-category/{category_id}")
async def get_skills_by_job_category(
    category_id: int,
    limit: int = Query(15, ge=1, le=50, description="Maximum number of skills to return"),
    db: Session = Depends(get_db)
):
    """
    Get most popular skills for a specific job category.
    
    Args:
        category_id: Job category ID
        limit: Maximum number of skills to return
        
    Returns:
        Skills popular in the specified job category
    """
    from sqlalchemy import text
    from fastapi import HTTPException
    from app.processors.nlp_engine import NLPEngine
    
    nlp_engine = NLPEngine()
    
    try:
        # Verify category exists
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Job category not found")
        
        query = text("""
            SELECT skill, COUNT(*) as job_count,
                   ROUND(COUNT(*) * 100.0 / (
                       SELECT COUNT(*) FROM jobs 
                       WHERE category_id = :category_id AND extracted_skills IS NOT NULL
                   ), 2) as percentage
            FROM (
                SELECT jsonb_array_elements_text(value) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE category_id = :category_id AND extracted_skills IS NOT NULL
            ) skills_data
            GROUP BY skill
            ORDER BY job_count DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"category_id": category_id, "limit": limit}).fetchall()
        
        return {
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description
            },
            "skills": [
                {
                    "name": row.skill,
                    "display_name": nlp_engine.get_display_name(row.skill),
                    "job_count": row.job_count,
                    "percentage": float(row.percentage)
                }
                for row in result
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error fetching skills for job category {category_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch skills for job category")

@router.get("/skills/growth-trends")
async def get_skill_growth_trends(
    days: int = Query(30, ge=7, le=365, description="Time period to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of skills to return"),
    db: Session = Depends(get_db)
):
    """
    Get skill growth trends by comparing current period to previous period.
    
    Args:
        days: Number of days for current period (previous period is same duration before that)
        limit: Maximum number of skills to return
        
    Returns:
        Skills with growth rates, sorted by highest growth
        
    Example:
        days=30 compares:
        - Current: Last 30 days
        - Previous: 30 days before that
        - Growth: ((current - previous) / previous) * 100
    """
    from sqlalchemy import text
    from app.processors.nlp_engine import NLPEngine
    
    nlp_engine = NLPEngine()
    
    try:
        # Calculate date ranges
        today = date.today()
        current_start = today - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        
        query = text("""
            WITH current_period AS (
                SELECT skill, COUNT(*) as count
                FROM (
                    SELECT jsonb_array_elements_text(value) as skill
                    FROM jobs, jsonb_each(extracted_skills)
                    WHERE extracted_skills IS NOT NULL 
                      AND posted_date >= :current_start
                      AND posted_date <= :today
                ) skills_data
                GROUP BY skill
            ),
            previous_period AS (
                SELECT skill, COUNT(*) as count
                FROM (
                    SELECT jsonb_array_elements_text(value) as skill
                    FROM jobs, jsonb_each(extracted_skills)
                    WHERE extracted_skills IS NOT NULL
                      AND posted_date >= :previous_start
                      AND posted_date < :current_start
                ) skills_data
                GROUP BY skill
            )
            SELECT 
                COALESCE(c.skill, p.skill) as skill,
                COALESCE(c.count, 0) as current_count,
                COALESCE(p.count, 0) as previous_count,
                CASE 
                    WHEN p.count > 0 THEN 
                        ROUND(((c.count::float - p.count::float) / p.count::float) * 100, 1)
                    WHEN c.count > 0 THEN 100.0
                    ELSE 0.0
                END as growth_rate
            FROM current_period c
            FULL OUTER JOIN previous_period p ON c.skill = p.skill
            WHERE COALESCE(c.count, 0) > 0  -- Only skills with current activity
            ORDER BY growth_rate DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            "current_start": current_start,
            "today": today,
            "previous_start": previous_start,
            "limit": limit
        }).fetchall()
        
        return [
            {
                "name": row.skill,
                "display_name": nlp_engine.get_display_name(row.skill),
                "current_count": row.current_count,
                "previous_count": row.previous_count,
                "growth_rate": float(row.growth_rate),
                "trend_direction": 'up' if row.growth_rate > 5 else 'down' if row.growth_rate < -5 else 'stable'
            }
            for row in result
        ]
        
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error calculating skill growth trends: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to calculate skill growth trends")

@router.get("/skills/categories")
async def get_skill_categories(db: Session = Depends(get_db)):
    """
    Get available skill categories with counts.
    
    Returns:
        List of skill categories with job counts
    """
    from sqlalchemy import text
    
    try:
        query = text("""
            SELECT category, COUNT(DISTINCT skill) as skill_count, COUNT(*) as job_count
            FROM (
                SELECT key as category, jsonb_array_elements_text(value) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE extracted_skills IS NOT NULL
            ) skills_data
            GROUP BY category
            ORDER BY job_count DESC
        """)
        
        result = db.execute(query).fetchall()
        
        return [
            {
                "category": row.category,
                "skill_count": row.skill_count,
                "job_count": row.job_count,
                "display_name": row.category.replace('_', ' ').title()
            }
            for row in result
        ]
        
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error fetching skill categories: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to fetch skill categories")

@router.get("/dashboard", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    days: int = Query(0, ge=0, le=365, description="Time period in days (0 for all time)"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics including job counts, company counts, and salary info.
    
    Filters by job posted date (not scrape date).
    
    Args:
        days: Time period in days (0 for all time)
    """
    stats = crud.get_dashboard_stats(db, days)
    return schemas.DashboardStats(**stats)

@router.get("/trending-skills", response_model=List[schemas.TrendingSkill])
async def get_trending_skills_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of skills to return"),
    db: Session = Depends(get_db)
):
    """
    Get trending skills for analytics dashboard.
    
    - **days**: Number of days to analyze for trends
    - **limit**: Maximum number of trending skills to return
    """
    trending_skills = crud.get_trending_skills(db, days=days, limit=limit)
    
    # trending_skills returns list of dicts with: name, job_count, avg_salary
    return [
        schemas.TrendingSkill(
            skill_id=0,  # Skills don't have IDs in JSONB storage
            name=skill["name"],
            category=None,  # Category not available from JSONB extraction
            job_count=skill["job_count"],
            avg_salary=skill["avg_salary"]
        )
        for skill in trending_skills
    ]

@router.get("/skill-trends", response_model=List[schemas.SkillTrend])
async def get_skill_trends_analytics(
    skill_id: Optional[int] = Query(None, description="Specific skill ID to analyze"),
    days: int = Query(90, ge=1, le=365, description="Number of days of trend data"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of trend records"),
    db: Session = Depends(get_db)
):
    """
    Get skill trend data for analytics.
    
    - **skill_id**: Optional specific skill to analyze
    - **days**: Number of days of trend data
    - **limit**: Maximum number of trend records
    """
    trends = crud.get_skill_trends(db, skill_id=skill_id, days=days, limit=limit)
    return [schemas.SkillTrend.from_orm(trend) for trend in trends]

@router.get("/salary-trends", response_model=List[schemas.SalaryTrend])
async def get_salary_trends(
    category_id: Optional[int] = Query(None, description="Job category to analyze"),
    location_id: Optional[int] = Query(None, description="Location to analyze"),
    experience_level: Optional[models.ExperienceLevel] = Query(None, description="Experience level"),
    days: int = Query(90, ge=1, le=365, description="Number of days of trend data"),
    db: Session = Depends(get_db)
):
    """
    Get salary trend data.
    
    - **category_id**: Optional job category filter
    - **location_id**: Optional location filter  
    - **experience_level**: Optional experience level filter
    - **days**: Number of days of trend data
    """
    cutoff_date = date.today() - timedelta(days=days)
    
    query = db.query(models.SalaryTrend).filter(
        models.SalaryTrend.date_recorded >= cutoff_date
    )
    
    if category_id:
        query = query.filter(models.SalaryTrend.category_id == category_id)
    
    if location_id:
        query = query.filter(models.SalaryTrend.location_id == location_id)
    
    if experience_level:
        query = query.filter(models.SalaryTrend.experience_level == experience_level)
    
    trends = query.order_by(models.SalaryTrend.date_recorded.desc()).limit(100).all()
    return [schemas.SalaryTrend.from_orm(trend) for trend in trends]

@router.get("/popular-companies", response_model=List[schemas.PopularCompany])
async def get_popular_companies(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of companies to return"),
    db: Session = Depends(get_db)
):
    """
    Get most popular companies based on active job postings.
    
    - **limit**: Maximum number of companies to return
    """
    week_ago = date.today() - timedelta(days=7)
    
    popular_companies = db.query(
        models.Company.id,
        models.Company.name,
        models.Company.industry,
        db.func.count(models.Job.id).filter(models.Job.is_active == True).label('active_jobs'),
        db.func.count(models.Job.id).filter(
            db.and_(
                models.Job.posted_date >= week_ago,
                models.Job.is_active == True
            )
        ).label('new_jobs_this_week')
    ).outerjoin(models.Job).group_by(
        models.Company.id, models.Company.name, models.Company.industry
    ).having(
        db.func.count(models.Job.id).filter(models.Job.is_active == True) > 0
    ).order_by(
        db.desc('active_jobs')
    ).limit(limit).all()
    
    return [
        schemas.PopularCompany(
            company_id=company.id,
            name=company.name,
            industry=company.industry,
            active_jobs=company.active_jobs,
            new_jobs_this_week=company.new_jobs_this_week
        )
        for company in popular_companies
    ]

@router.get("/job-statistics")
async def get_job_statistics(db: Session = Depends(get_db)):
    """
    Get various job market statistics.
    """
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Job counts by time period - BUSINESS LOGIC: Only count tech jobs
    total_jobs = db.query(models.Job).filter(models.Job.is_tech_job == True).count()
    active_jobs = db.query(models.Job).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    ).count()
    jobs_this_week = db.query(models.Job).filter(
        and_(models.Job.posted_date >= week_ago, models.Job.is_tech_job == True)
    ).count()
    jobs_this_month = db.query(models.Job).filter(
        and_(models.Job.posted_date >= month_ago, models.Job.is_tech_job == True)
    ).count()
    
    # Employment type distribution
    employment_types = db.query(
        models.Job.employment_type,
        db.func.count(models.Job.id).label('count')
    ).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    ).group_by(
        models.Job.employment_type
    ).all()
    
    # Experience level distribution
    experience_levels = db.query(
        models.Job.experience_level,
        db.func.count(models.Job.id).label('count')
    ).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    ).group_by(
        models.Job.experience_level
    ).all()
    
    # Salary statistics
    salary_stats = db.query(
        db.func.avg(models.Job.salary_min).label('avg_min_salary'),
        db.func.avg(models.Job.salary_max).label('avg_max_salary'),
        db.func.min(models.Job.salary_min).label('min_salary'),
        db.func.max(models.Job.salary_max).label('max_salary')
    ).filter(
        db.and_(
            models.Job.is_active == True,
            models.Job.is_tech_job == True,
            models.Job.salary_min.isnot(None),
            models.Job.salary_max.isnot(None)
        )
    ).first()
    
    return {
        "job_counts": {
            "total": total_jobs,
            "active": active_jobs,
            "this_week": jobs_this_week,
            "this_month": jobs_this_month
        },
        "employment_types": [
            {"type": et.employment_type.value if et.employment_type else "unknown", "count": et.count}
            for et in employment_types
        ],
        "experience_levels": [
            {"level": el.experience_level.value if el.experience_level else "unknown", "count": el.count}
            for el in experience_levels
        ],
        "salary_statistics": {
            "avg_min_salary": float(salary_stats.avg_min_salary) if salary_stats.avg_min_salary else None,
            "avg_max_salary": float(salary_stats.avg_max_salary) if salary_stats.avg_max_salary else None,
            "min_salary": int(salary_stats.min_salary) if salary_stats.min_salary else None,
            "max_salary": int(salary_stats.max_salary) if salary_stats.max_salary else None
        }
    }

@router.get("/location-statistics")
async def get_location_statistics(db: Session = Depends(get_db)):
    """
    Get job statistics by location.
    """
    location_stats = db.query(
        models.Location.id,
        models.Location.city,
        models.Location.region,
        db.func.count(models.Job.id).filter(
            and_(models.Job.is_active == True, models.Job.is_tech_job == True)
        ).label('active_jobs'),
        db.func.avg(models.Job.salary_max).filter(models.Job.is_tech_job == True).label('avg_salary')
    ).outerjoin(models.Job).group_by(
        models.Location.id, models.Location.city, models.Location.region
    ).having(
        db.func.count(models.Job.id).filter(
            and_(models.Job.is_active == True, models.Job.is_tech_job == True)
        ) > 0
    ).order_by(
        db.desc('active_jobs')
    ).all()
    
    return [
        {
            "location_id": loc.id,
            "city": loc.city,
            "region": loc.region,
            "active_jobs": loc.active_jobs,
            "avg_salary": float(loc.avg_salary) if loc.avg_salary else None
        }
        for loc in location_stats
    ]

@router.get("/tracked-keywords")
async def get_tracked_keywords():
    """
    Get all search terms and skills taxonomy that the platform monitors.
    
    Returns:
        Dictionary containing:
        - search_terms: List of job search terms used by the scraper
        - skills_taxonomy: Skills organized by category with display names
    """
    from app.scrapers.seek_scraper import SeekScraper
    from app.processors.nlp_engine import NLPEngine
    
    try:
        # Get search terms from scraper
        scraper = SeekScraper()
        search_terms = scraper.get_search_terms()
        
        # Get skills taxonomy from NLP engine
        nlp_engine = NLPEngine()
        
        # Organize skills by category with display names
        skills_taxonomy = {}
        for category, skills in nlp_engine.tech_skills.items():
            skills_taxonomy[category] = {
                "display_name": category.replace('_', ' ').title(),
                "skills": [
                    {
                        "name": skill,
                        "display_name": nlp_engine.get_display_name(skill)
                    }
                    for skill in sorted(skills)
                ]
            }
        
        return {
            "search_terms": search_terms,
            "skills_taxonomy": skills_taxonomy,
            "total_search_terms": len(search_terms),
            "total_skill_categories": len(skills_taxonomy),
            "total_skills": sum(len(cat["skills"]) for cat in skills_taxonomy.values())
        }
        
    except Exception as e:
        from app.core.logging import get_logger
        from fastapi import HTTPException
        logger = get_logger(__name__)
        logger.error(f"Error fetching tracked keywords: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tracked keywords")

@router.get("/skill-categories")
async def get_skill_category_statistics(db: Session = Depends(get_db)):
    """
    Get job statistics by skill category.
    """
    category_stats = db.query(
        models.Skill.category,
        db.func.count(db.distinct(models.JobSkill.job_id)).label('job_count'),
        db.func.count(models.Skill.id).label('skill_count'),
        db.func.avg(models.Job.salary_max).label('avg_salary')
    ).outerjoin(models.JobSkill).outerjoin(models.Job).filter(
        and_(models.Job.is_active == True, models.Job.is_tech_job == True)
    ).group_by(
        models.Skill.category
    ).order_by(
        db.desc('job_count')
    ).all()
    
    return [
        {
            "category": cat.category.value if cat.category else "unknown",
            "job_count": cat.job_count,
            "skill_count": cat.skill_count,
            "avg_salary": float(cat.avg_salary) if cat.avg_salary else None
        }
        for cat in category_stats
    ]