"""
TechInsights  - Job Repository
Repository for job-related database operations
"""

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, func, and_, or_, text, desc, asc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from src.models.job import Job, ExperienceLevel, EmploymentType, RemoteWorkOption
from src.models.company import Company
from src.models.data_source import DataSource
from src.models.job_category import JobCategory
from src.models.job_tech_requirement import JobTechRequirement
from src.models.tech_stack import TechStack
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class JobSearchFilters:
    """Data class for job search filters."""
    
    def __init__(
        self,
        keywords: Optional[str] = None,
        tech_stacks: Optional[List[str]] = None,
        tech_stack_operator: str = "AND",
        experience_level: Optional[ExperienceLevel] = None,
        employment_type: Optional[EmploymentType] = None,
        remote_work_option: Optional[RemoteWorkOption] = None,
        location: Optional[str] = None,
        city: Optional[str] = None,
        sources: Optional[List[str]] = None,
        company_names: Optional[List[str]] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        posted_since_days: Optional[int] = None,
        is_active: bool = True,
        exclude_duplicates: bool = True,
        min_quality_score: Optional[float] = None
    ):
        self.keywords = keywords
        self.tech_stacks = tech_stacks or []
        self.tech_stack_operator = tech_stack_operator
        self.experience_level = experience_level
        self.employment_type = employment_type
        self.remote_work_option = remote_work_option
        self.location = location
        self.city = city
        self.sources = sources or []
        self.company_names = company_names or []
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.posted_since_days = posted_since_days
        self.is_active = is_active
        self.exclude_duplicates = exclude_duplicates
        self.min_quality_score = min_quality_score


class JobRepository(BaseRepository[Job]):
    """Repository for job-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Job, db)
    
    # ========================================================================
    # SPECIALIZED QUERY METHODS
    # ========================================================================
    
    def get_job_with_details(self, job_id: int) -> Optional[Job]:
        """
        Get a job with all related data (company, tech requirements, etc.).
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            Optional[Job]: Job with eagerly loaded relationships
        """
        try:
            stmt = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    joinedload(Job.data_source),
                    joinedload(Job.job_category),
                    selectinload(Job.tech_requirements).joinedload(JobTechRequirement.tech_stack)
                )
                .where(Job.job_id == job_id)
            )
            
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting job details for ID {job_id}: {e}")
            raise
    
    def search_jobs(
        self,
        filters: JobSearchFilters,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "posted_date",
        order_desc: bool = True
    ) -> Tuple[List[Job], int]:
        """
        Search jobs with advanced filtering and pagination.
        
        Args:
            filters: JobSearchFilters object with search criteria
            offset: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            Tuple[List[Job], int]: (jobs, total_count)
        """
        try:
            # Base query with relationships
            base_query = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    joinedload(Job.data_source),
                    selectinload(Job.tech_requirements).joinedload(JobTechRequirement.tech_stack)
                )
            )
            
            # Build WHERE conditions
            conditions = self._build_search_conditions(filters)
            
            # Apply conditions to main query
            if conditions:
                query = base_query.where(and_(*conditions))
            else:
                query = base_query
            
            # Count query for total results
            count_query = select(func.count(Job.job_id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            # Apply ordering
            if hasattr(Job, order_by):
                order_field = getattr(Job, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute queries
            total_count = self.db.execute(count_query).scalar()
            jobs = self.db.execute(query).scalars().all()
            
            logger.debug(f"Job search returned {len(jobs)} of {total_count} total jobs")
            return jobs, total_count
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            raise
    
    def search_jobs_with_fulltext(
        self,
        search_text: str,
        filters: Optional[JobSearchFilters] = None,
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[Job], int]:
        """
        Search jobs using PostgreSQL full-text search.
        
        Args:
            search_text: Text to search for
            filters: Optional additional filters
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple[List[Job], int]: (jobs with relevance scores, total_count)
        """
        try:
            # Build full-text search query
            search_vector = func.to_tsvector('english', Job.description_cleaned)
            search_query = func.plainto_tsquery('english', search_text)
            relevance = func.ts_rank(search_vector, search_query)
            
            # Base query with full-text search
            base_query = (
                select(Job, relevance.label('relevance'))
                .options(
                    joinedload(Job.company),
                    joinedload(Job.data_source)
                )
                .where(search_vector.op('@@')(search_query))
            )
            
            # Add additional filters if provided
            if filters:
                additional_conditions = self._build_search_conditions(filters)
                if additional_conditions:
                    base_query = base_query.where(and_(*additional_conditions))
            
            # Count query
            count_query = (
                select(func.count(Job.job_id))
                .where(search_vector.op('@@')(search_query))
            )
            
            if filters:
                additional_conditions = self._build_search_conditions(filters)
                if additional_conditions:
                    count_query = count_query.where(and_(*additional_conditions))
            
            # Order by relevance
            query = base_query.order_by(desc('relevance')).offset(offset).limit(limit)
            
            # Execute queries
            total_count = self.db.execute(count_query).scalar()
            results = self.db.execute(query).all()
            
            # Extract jobs (first element of each tuple)
            jobs = [result[0] for result in results]
            
            logger.debug(f"Full-text search returned {len(jobs)} of {total_count} total jobs")
            return jobs, total_count
            
        except Exception as e:
            logger.error(f"Error in full-text job search: {e}")
            raise
    
    def get_jobs_by_company(
        self,
        company_id: int,
        is_active: bool = True,
        limit: int = 50
    ) -> List[Job]:
        """
        Get jobs posted by a specific company.
        
        Args:
            company_id: Company ID
            is_active: Whether to only return active jobs
            limit: Maximum number of jobs to return
            
        Returns:
            List[Job]: Jobs posted by the company
        """
        try:
            stmt = (
                select(Job)
                .options(joinedload(Job.data_source))
                .where(Job.company_id == company_id)
                .order_by(desc(Job.posted_date))
                .limit(limit)
            )
            
            if is_active:
                stmt = stmt.where(Job.is_active == True)
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting jobs for company {company_id}: {e}")
            raise
    
    def get_jobs_by_tech_stack(
        self,
        tech_stack_names: List[str],
        operator: str = "AND",
        limit: int = 100
    ) -> List[Job]:
        """
        Get jobs that require specific technology stacks.
        
        Args:
            tech_stack_names: List of technology names to search for
            operator: "AND" or "OR" for combining tech requirements
            limit: Maximum number of jobs to return
            
        Returns:
            List[Job]: Jobs requiring the specified technologies
        """
        try:
            # Subquery to find jobs with required tech stacks
            tech_subquery = (
                select(JobTechRequirement.job_id)
                .join(TechStack)
                .where(TechStack.normalized_name.in_(tech_stack_names))
                .group_by(JobTechRequirement.job_id)
            )
            
            if operator.upper() == "AND":
                # Job must have ALL specified technologies
                tech_subquery = tech_subquery.having(
                    func.count(JobTechRequirement.tech_id) == len(tech_stack_names)
                )
            
            # Main query
            stmt = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    selectinload(Job.tech_requirements).joinedload(JobTechRequirement.tech_stack)
                )
                .where(Job.job_id.in_(tech_subquery))
                .where(Job.is_active == True)
                .order_by(desc(Job.posted_date))
                .limit(limit)
            )
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting jobs by tech stacks {tech_stack_names}: {e}")
            raise
    
    def get_recent_jobs(
        self,
        days: int = 7,
        sources: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Job]:
        """
        Get recently posted jobs.
        
        Args:
            days: Number of days back to search
            sources: Optional list of source names to filter by
            limit: Maximum number of jobs to return
            
        Returns:
            List[Job]: Recently posted jobs
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            stmt = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    joinedload(Job.data_source)
                )
                .where(Job.posted_date >= cutoff_date)
                .where(Job.is_active == True)
                .order_by(desc(Job.posted_date))
                .limit(limit)
            )
            
            if sources:
                stmt = stmt.join(DataSource).where(DataSource.source_name.in_(sources))
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting recent jobs: {e}")
            raise
    
    def find_similar_jobs(
        self,
        job_id: int,
        similarity_threshold: float = 0.3,
        limit: int = 10
    ) -> List[Job]:
        """
        Find jobs similar to a given job based on tech requirements.
        
        Args:
            job_id: Reference job ID
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of similar jobs to return
            
        Returns:
            List[Job]: Similar jobs ordered by similarity
        """
        try:
            # Get tech requirements for the reference job
            reference_job_techs = (
                self.db.query(JobTechRequirement.tech_id)
                .filter(JobTechRequirement.job_id == job_id)
                .all()
            )
            
            if not reference_job_techs:
                return []
            
            reference_tech_ids = [tech.tech_id for tech in reference_job_techs]
            
            # Find jobs with overlapping tech requirements
            # Using SQL to calculate Jaccard similarity
            similarity_query = text("""
                WITH reference_techs AS (
                    SELECT unnest(:tech_ids) as tech_id
                ),
                job_similarities AS (
                    SELECT 
                        j.job_id,
                        COUNT(DISTINCT jtr.tech_id) as common_techs,
                        (
                            SELECT COUNT(DISTINCT tech_id) 
                            FROM job_tech_requirements 
                            WHERE job_id = j.job_id
                        ) as job_tech_count,
                        :ref_tech_count as ref_tech_count
                    FROM jobs j
                    JOIN job_tech_requirements jtr ON j.job_id = jtr.job_id
                    JOIN reference_techs rt ON jtr.tech_id = rt.tech_id
                    WHERE j.job_id != :job_id 
                        AND j.is_active = true
                    GROUP BY j.job_id
                    HAVING COUNT(DISTINCT jtr.tech_id) > 0
                )
                SELECT 
                    job_id,
                    common_techs::float / (job_tech_count + ref_tech_count - common_techs) as similarity
                FROM job_similarities
                WHERE common_techs::float / (job_tech_count + ref_tech_count - common_techs) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            
            result = self.db.execute(
                similarity_query,
                {
                    'tech_ids': reference_tech_ids,
                    'ref_tech_count': len(reference_tech_ids),
                    'job_id': job_id,
                    'threshold': similarity_threshold,
                    'limit': limit
                }
            )
            
            similar_job_ids = [row.job_id for row in result]
            
            if not similar_job_ids:
                return []
            
            # Get the actual job objects
            stmt = (
                select(Job)
                .options(
                    joinedload(Job.company),
                    joinedload(Job.data_source)
                )
                .where(Job.job_id.in_(similar_job_ids))
                .order_by(desc(Job.posted_date))
            )
            
            jobs_result = self.db.execute(stmt)
            return jobs_result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error finding similar jobs for job {job_id}: {e}")
            raise
    
    # ========================================================================
    # ANALYTICS AND AGGREGATION METHODS
    # ========================================================================
    
    def get_job_counts_by_criteria(
        self,
        filters: Optional[JobSearchFilters] = None
    ) -> Dict[str, Any]:
        """
        Get job counts grouped by various criteria.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Dict[str, Any]: Dictionary with counts by different criteria
        """
        try:
            base_conditions = []
            if filters:
                base_conditions = self._build_search_conditions(filters)
            
            # Base query builder
            def build_count_query(group_field, join_table=None):
                query = select(group_field, func.count(Job.job_id).label('count'))
                if join_table:
                    query = query.join(join_table)
                if base_conditions:
                    query = query.where(and_(*base_conditions))
                return query.group_by(group_field)
            
            # Count by experience level
            exp_query = build_count_query(Job.experience_level)
            exp_counts = {str(row[0]): row[1] for row in self.db.execute(exp_query) if row[0]}
            
            # Count by employment type
            emp_query = build_count_query(Job.employment_type)
            emp_counts = {str(row[0]): row[1] for row in self.db.execute(emp_query) if row[0]}
            
            # Count by data source
            source_query = build_count_query(DataSource.source_name, DataSource)
            source_counts = {row[0]: row[1] for row in self.db.execute(source_query)}
            
            # Count by location (city)
            location_query = build_count_query(Job.city)
            location_counts = {row[0]: row[1] for row in self.db.execute(location_query) if row[0]}
            
            # Total count
            total_query = select(func.count(Job.job_id))
            if base_conditions:
                total_query = total_query.where(and_(*base_conditions))
            total_count = self.db.execute(total_query).scalar()
            
            return {
                'total': total_count,
                'by_experience_level': exp_counts,
                'by_employment_type': emp_counts,
                'by_source': source_counts,
                'by_location': location_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting job counts by criteria: {e}")
            raise
    
    def get_salary_statistics(
        self,
        filters: Optional[JobSearchFilters] = None
    ) -> Dict[str, float]:
        """
        Get salary statistics for jobs matching the criteria.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Dict[str, float]: Salary statistics (min, max, avg, median)
        """
        try:
            conditions = [Job.salary_min.isnot(None), Job.salary_max.isnot(None)]
            
            if filters:
                conditions.extend(self._build_search_conditions(filters))
            
            # Query for salary statistics
            stmt = (
                select(
                    func.min(Job.salary_min).label('min_salary'),
                    func.max(Job.salary_max).label('max_salary'),
                    func.avg((Job.salary_min + Job.salary_max) / 2).label('avg_salary'),
                    func.percentile_cont(0.5).within_group((Job.salary_min + Job.salary_max) / 2).label('median_salary')
                )
                .where(and_(*conditions))
            )
            
            result = self.db.execute(stmt).one()
            
            return {
                'min_salary': float(result.min_salary) if result.min_salary else 0.0,
                'max_salary': float(result.max_salary) if result.max_salary else 0.0,
                'avg_salary': float(result.avg_salary) if result.avg_salary else 0.0,
                'median_salary': float(result.median_salary) if result.median_salary else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting salary statistics: {e}")
            raise
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _build_search_conditions(self, filters: JobSearchFilters) -> List:
        """
        Build SQLAlchemy conditions from search filters.
        
        Args:
            filters: JobSearchFilters object
            
        Returns:
            List: List of SQLAlchemy conditions
        """
        conditions = []
        
        # Active status filter
        if filters.is_active is not None:
            conditions.append(Job.is_active == filters.is_active)
        
        # Exclude duplicates
        if filters.exclude_duplicates:
            conditions.append(Job.is_duplicate == False)
        
        # Experience level filter
        if filters.experience_level:
            conditions.append(Job.experience_level == filters.experience_level)
        
        # Employment type filter
        if filters.employment_type:
            conditions.append(Job.employment_type == filters.employment_type)
        
        # Remote work option filter
        if filters.remote_work_option:
            conditions.append(Job.remote_work_option == filters.remote_work_option)
        
        # Location filters
        if filters.location:
            conditions.append(Job.location.ilike(f"%{filters.location}%"))
        
        if filters.city:
            conditions.append(Job.city.ilike(f"%{filters.city}%"))
        
        # Salary range filter
        if filters.salary_min:
            conditions.append(Job.salary_min >= filters.salary_min)
        
        if filters.salary_max:
            conditions.append(Job.salary_max <= filters.salary_max)
        
        # Posted date filter
        if filters.posted_since_days:
            cutoff_date = datetime.now() - timedelta(days=filters.posted_since_days)
            conditions.append(Job.posted_date >= cutoff_date)
        
        # Data quality filter
        if filters.min_quality_score:
            conditions.append(Job.data_quality_score >= filters.min_quality_score)
        
        # Source filter
        if filters.sources:
            source_subquery = (
                select(DataSource.source_id)
                .where(DataSource.source_name.in_(filters.sources))
            )
            conditions.append(Job.source_id.in_(source_subquery))
        
        # Company filter
        if filters.company_names:
            company_subquery = (
                select(Company.company_id)
                .where(Company.company_name.in_(filters.company_names))
            )
            conditions.append(Job.company_id.in_(company_subquery))
        
        return conditions
    
    def create_job_from_external(self, job_data: Dict[str, Any]) -> Job:
        """
        Create a job record from external scraped data.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Job: Created job instance
        """
        try:
            # Create the job record
            job = self.create(job_data)
            
            logger.info(f"Created job from external data: {job.external_job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating job from external data: {e}")
            raise
    
    def mark_job_as_inactive(self, job_id: int) -> bool:
        """
        Mark a job as inactive (no longer available).
        
        Args:
            job_id: Job ID to mark as inactive
            
        Returns:
            bool: True if job was updated, False if not found
        """
        try:
            return self.update(job_id, {'is_active': False}) is not None
        except Exception as e:
            logger.error(f"Error marking job {job_id} as inactive: {e}")
            raise

