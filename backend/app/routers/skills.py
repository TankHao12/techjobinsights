"""
Skills API Router
Individual skill endpoints for detailed analytics
US-4.1: Create Skills Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional

from app.database import get_db
from app import schemas
from app import models

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/pairs", response_model=List[schemas.SkillPair])
async def get_skill_pairs(
    limit: int = Query(15, ge=1, le=50, description="Maximum number of skill pairs to return"),
    db: Session = Depends(get_db)
):
    """
    Get common skill pairs based on co-occurrence in job postings.

    Args:
        limit: Maximum number of pairs to return

    Returns:
        Array of skill pairs with co-occurrence statistics
    """
    try:
        query = text("""
            WITH skill_pairs AS (
                SELECT
                    s1.skill as skill1,
                    s2.skill as skill2,
                    COUNT(DISTINCT s1.id) as job_count
                FROM (
                    SELECT DISTINCT j.id, jsonb_array_elements_text(value) as skill
                    FROM jobs j, jsonb_each(j.extracted_skills)
                    WHERE j.extracted_skills IS NOT NULL AND j.is_tech_job = TRUE
                ) s1
                JOIN (
                    SELECT DISTINCT j.id, jsonb_array_elements_text(value) as skill
                    FROM jobs j, jsonb_each(j.extracted_skills)
                    WHERE j.extracted_skills IS NOT NULL AND j.is_tech_job = TRUE
                ) s2 ON s1.id = s2.id AND s1.skill < s2.skill
                GROUP BY s1.skill, s2.skill
                HAVING COUNT(DISTINCT s1.id) > 5
            )
            SELECT
                skill1,
                skill2,
                job_count,
                ROUND(job_count * 100.0 / (SELECT COUNT(DISTINCT id) FROM jobs WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE), 2) as percentage
            FROM skill_pairs
            ORDER BY job_count DESC
            LIMIT :limit
        """)

        result = db.execute(query, {"limit": limit}).fetchall()

        return [
            {
                "skill1": row.skill1,
                "skill2": row.skill2,
                "job_count": row.job_count,
                "percentage": float(row.percentage),
                "strength": "high" if row.job_count > 50 else "medium" if row.job_count > 20 else "low"
            }
            for row in result
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch skill pairs: {str(e)}")

@router.get("/compare", response_model=List[schemas.SkillComparison])
async def compare_skills(
    skills: str = Query(..., description="Comma-separated skill names to compare"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple skills side-by-side.

    Args:
        skills: Comma-separated list of skill names (2-3 skills)

    Returns:
        Array of skill comparison data
    """
    try:
        skill_list = [s.strip().lower() for s in skills.split(',')]

        if len(skill_list) < 2 or len(skill_list) > 3:
            raise HTTPException(status_code=400, detail="Please provide 2-3 skills to compare")

        comparisons = []

        for skill_name in skill_list:
            # Get basic skill metrics
            skill_query = text("""
                SELECT skill, COUNT(DISTINCT job_id) as job_count,
                       ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT COUNT(DISTINCT id) FROM jobs WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE), 2) as percentage
                FROM (
                    SELECT id as job_id, jsonb_array_elements_text(value) as skill
                    FROM jobs, jsonb_each(extracted_skills)
                    WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                ) skills_data
                WHERE LOWER(skill) = :skill_name
                GROUP BY skill
            """)

            result = db.execute(skill_query, {"skill_name": skill_name}).fetchone()

            if result:
                # Get company count
                company_query = text("""
                    SELECT COUNT(DISTINCT j.company_id) as company_count
                    FROM jobs j
                    WHERE j.extracted_skills IS NOT NULL
                      AND j.is_tech_job = TRUE
                      AND j.id IN (
                          SELECT job_id FROM (
                              SELECT j2.id as job_id, jsonb_array_elements_text(value) as skill
                              FROM jobs j2, jsonb_each(j2.extracted_skills)
                              WHERE j2.extracted_skills IS NOT NULL AND j2.is_tech_job = TRUE
                          ) skill_jobs
                          WHERE skill_jobs.skill = :skill_name
                      )
                """)

                company_result = db.execute(company_query, {"skill_name": result.skill}).fetchone()

                comparisons.append({
                    "skill": result.skill,
                    "demand": result.job_count,
                    "growth_rate": 12.5,  # TODO: Calculate actual growth
                    "companies_using": company_result.company_count if company_result else 0,
                    "percentage": float(result.percentage),
                    "trend_data": [  # Mock trend data
                        {"date": "2024-10-01", "count": max(1, result.job_count - 10)},
                        {"date": "2024-11-01", "count": result.job_count},
                        {"date": "2024-11-15", "count": result.job_count + 5},
                    ]
                })
            else:
                # Skill not found
                comparisons.append({
                    "skill": skill_name,
                    "demand": 0,
                    "growth_rate": 0.0,
                    "companies_using": 0,
                    "percentage": 0.0,
                    "trend_data": []
                })

        return comparisons

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare skills: {str(e)}")

@router.get("/recommendations")
async def get_skill_recommendations(
    known_skills: str = Query(..., description="Comma-separated list of skills you already know"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of recommendations"),
    db: Session = Depends(get_db)
):
    """
    Get skill recommendations based on skills you already know.
    
    Returns skills that frequently appear together with your known skills,
    helping you decide what to learn next to maximize job opportunities.
    
    Args:
        known_skills: Comma-separated list of skills you know (e.g., "python,sql")
        limit: Maximum number of recommendations to return
        
    Returns:
        List of recommended skills with relevance scores and job counts
    """
    try:
        skill_list = [s.strip().lower() for s in known_skills.split(',') if s.strip()]
        
        if not skill_list:
            raise HTTPException(status_code=400, detail="Please provide at least one skill")
        
        # Find skills that frequently appear with the known skills
        # Use the same pattern as the working /pairs endpoint
        skill_conditions = " OR ".join([f"LOWER(skill) = '{skill}'" for skill in skill_list])
        exclude_conditions = " AND ".join([f"LOWER(skill) != '{skill}'" for skill in skill_list])
        
        query = text(f"""
            WITH all_skills AS (
                -- Extract all skills from all jobs (similar to /pairs endpoint pattern)
                SELECT DISTINCT id as job_id, LOWER(jsonb_array_elements_text(value)) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
            ),
            jobs_with_user_skills AS (
                -- Jobs that have at least one of the user's skills
                SELECT DISTINCT job_id
                FROM all_skills
                WHERE {skill_conditions}
            ),
            recommended_skills AS (
                -- Find other skills in those jobs
                SELECT 
                    s.skill,
                    COUNT(DISTINCT s.job_id) as jobs_with_skill,
                    COUNT(DISTINCT s.job_id) * 100.0 / NULLIF((SELECT COUNT(*) FROM jobs_with_user_skills), 0) as relevance_score
                FROM all_skills s
                JOIN jobs_with_user_skills jwu ON s.job_id = jwu.job_id
                WHERE {exclude_conditions}
                GROUP BY s.skill
                HAVING COUNT(DISTINCT s.job_id) > 5
            )
            SELECT 
                skill,
                jobs_with_skill as job_count,
                ROUND(relevance_score::numeric, 1) as relevance_score,
                ROUND((jobs_with_skill * 100.0 / NULLIF((SELECT COUNT(DISTINCT id) FROM jobs WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE), 0))::numeric, 2) as market_demand
            FROM recommended_skills
            ORDER BY relevance_score DESC, job_count DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit}).fetchall()
        
        if not result:
            return {
                "known_skills": skill_list,
                "recommendations": [],
                "message": "No recommendations found. Try different skills or check spelling."
            }
        
        return {
            "known_skills": skill_list,
            "recommendations": [
                {
                    "skill": row.skill,
                    "job_count": row.job_count,
                    "relevance_score": float(row.relevance_score),
                    "market_demand": float(row.market_demand),
                    "reason": f"Appears in {row.relevance_score:.0f}% of jobs that require your skills"
                }
                for row in result
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/search", response_model=List[schemas.SkillWithStats])
async def search_skills(
    query: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Skill category filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for skills by name.

    Args:
        query: Search term
        category: Optional skill category filter
        limit: Maximum number of results

    Returns:
        Array of matching skills with stats
    """
    try:
        search_query = text("""
            SELECT skill, COUNT(DISTINCT job_id) as job_count,
                   ROUND(COUNT(DISTINCT job_id) * 100.0 / (SELECT COUNT(DISTINCT id) FROM jobs WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE), 2) as percentage
            FROM (
                SELECT id as job_id, jsonb_array_elements_text(value) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
                  AND (:category IS NULL OR key = :category)
            ) skills_data
            WHERE LOWER(skill) LIKE LOWER(:query)
            GROUP BY skill
            ORDER BY job_count DESC
            LIMIT :limit
        """)

        search_pattern = f"%{query}%"
        result = db.execute(search_query, {
            "query": search_pattern,
            "category": category,
            "limit": limit
        }).fetchall()

        return [
            {
                "id": idx + 1,
                "name": row.skill,
                "display_name": row.skill,
                "category": category or "not_specified",
                "skill_type": "technical",
                "popularity_score": int(row.percentage),
                "job_count": row.job_count,
                "required_count": row.job_count,
                "primary_count": row.job_count,
                "percentage": float(row.percentage)
            }
            for idx, row in enumerate(result)
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search skills: {str(e)}")

@router.get("/{skill_name}", response_model=schemas.SkillDetail)
async def get_skill_detail(
    skill_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific skill.

    Returns:
        Comprehensive skill analytics including demand, trends, companies, and related skills
    """
    try:
        # Normalize skill name (remove URL formatting)
        normalized_skill = skill_name.replace('-', ' ').replace('_', ' ').lower()

        # Get basic skill information
        skill_query = text("""
            SELECT skill, COUNT(*) as job_count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE), 2) as percentage
            FROM (
                SELECT jsonb_array_elements_text(value) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
            ) skills_data
            WHERE LOWER(skill) = :skill_name
            GROUP BY skill
        """)

        skill_result = db.execute(skill_query, {"skill_name": normalized_skill}).fetchone()

        if not skill_result:
            raise HTTPException(status_code=404, detail="Skill not found")

        # Get skill category
        category_query = text("""
            SELECT category_data.key as category
            FROM (
                SELECT key, jsonb_array_elements_text(value) as skill
                FROM jobs, jsonb_each(extracted_skills)
                WHERE extracted_skills IS NOT NULL AND is_tech_job = TRUE
            ) category_data
            WHERE category_data.skill = :skill_name
            LIMIT 1
        """)

        category_result = db.execute(category_query, {"skill_name": skill_result.skill}).fetchone()
        skill_category = category_result.category if category_result else "other"

        # Get top companies using this skill
        companies_query = text("""
            SELECT c.name, COUNT(*) as job_count
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.extracted_skills IS NOT NULL
              AND j.is_tech_job = TRUE
              AND j.id IN (
                  SELECT job_id FROM (
                      SELECT j2.id as job_id, jsonb_array_elements_text(value) as skill
                      FROM jobs j2, jsonb_each(j2.extracted_skills)
                      WHERE j2.extracted_skills IS NOT NULL AND j2.is_tech_job = TRUE
                  ) skill_jobs
                  WHERE skill_jobs.skill = :skill_name
              )
            GROUP BY c.id, c.name
            ORDER BY job_count DESC
            LIMIT 10
        """)

        companies_result = db.execute(companies_query, {"skill_name": skill_result.skill}).fetchall()

        # Get related skills (co-occurrence)
        related_query = text("""
            WITH skill_jobs AS (
                SELECT job_id FROM (
                    SELECT j.id as job_id, jsonb_array_elements_text(value) as skill
                    FROM jobs j, jsonb_each(j.extracted_skills)
                    WHERE j.extracted_skills IS NOT NULL AND j.is_tech_job = TRUE
                ) skill_data
                WHERE skill_data.skill = :skill_name
            ),
            related_skills AS (
                SELECT skill_data2.skill as related_skill, COUNT(*) as co_occurrence
                FROM (
                    SELECT j.id as job_id, jsonb_array_elements_text(value) as skill
                    FROM jobs j, jsonb_each(j.extracted_skills)
                    WHERE j.extracted_skills IS NOT NULL AND j.is_tech_job = TRUE
                ) skill_data2
                WHERE skill_data2.job_id IN (SELECT job_id FROM skill_jobs)
                  AND skill_data2.skill != :skill_name
                GROUP BY skill_data2.skill
            )
            SELECT related_skill, co_occurrence,
                   ROUND(co_occurrence * 100.0 / :total_jobs, 2) as percentage
            FROM related_skills
            ORDER BY co_occurrence DESC
            LIMIT 5
        """)

        related_result = db.execute(related_query, {
            "skill_name": skill_result.skill,
            "total_jobs": skill_result.job_count
        }).fetchall()

        # Get 90-day trend data (mock for now since we don't have historical data)
        # TODO: Implement actual trend calculation with historical data
        trend_data = [
            {"date": "2024-10-01", "count": max(1, skill_result.job_count - 20)},
            {"date": "2024-10-15", "count": max(1, skill_result.job_count - 10)},
            {"date": "2024-11-01", "count": skill_result.job_count},
            {"date": "2024-11-15", "count": skill_result.job_count + 5},
        ]

        # Calculate growth rate (mock)
        growth_rate = 12.5  # TODO: Calculate actual growth rate

        return schemas.SkillDetail(
            name=skill_result.skill,
            category=skill_category,
            current_demand={
                "job_count": skill_result.job_count,
                "percentage": float(skill_result.percentage),
                "rank": 1  # TODO: Calculate actual rank
            },
            growth_rate=growth_rate,
            trend_data=trend_data,
            top_companies=[
                {"name": comp.name, "job_count": comp.job_count}
                for comp in companies_result
            ],
            related_skills=[
                {
                    "skill": rel.related_skill,
                    "co_occurrence_percentage": float(rel.percentage),
                    "job_count": rel.co_occurrence
                }
                for rel in related_result
            ],
            # TODO: Add experience distribution and location breakdown
            experience_distribution={},
            location_breakdown=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch skill details: {str(e)}")