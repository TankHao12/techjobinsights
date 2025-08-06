"""
TechInsights  - Job Tech Requirement Repository
Repository for job technology requirement operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
import logging

from src.models.job_tech_requirement import JobTechRequirement, RequirementType
from src.models.tech_stack import TechStack
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class JobTechRequirementRepository(BaseRepository[JobTechRequirement]):
    """Repository for job technology requirement operations."""
    
    def __init__(self, db: Session):
        super().__init__(JobTechRequirement, db)
    
    def get_by_job_and_tech(self, job_id: int, tech_id: int) -> Optional[JobTechRequirement]:
        """Get requirement by job and tech IDs."""
        try:
            stmt = (
                select(JobTechRequirement)
                .where(
                    and_(
                        JobTechRequirement.job_id == job_id,
                        JobTechRequirement.tech_id == tech_id
                    )
                )
            )
            
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting requirement for job {job_id} and tech {tech_id}: {e}")
            raise
    
    def get_requirements_for_job(self, job_id: int) -> List[JobTechRequirement]:
        """Get all tech requirements for a job."""
        try:
            stmt = (
                select(JobTechRequirement)
                .options(joinedload(JobTechRequirement.tech_stack))
                .where(JobTechRequirement.job_id == job_id)
                .order_by(JobTechRequirement.confidence_score.desc())
            )
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting requirements for job {job_id}: {e}")
            raise
    
    def create_or_update_requirement(
        self,
        job_id: int,
        tech_id: int,
        requirement_data: Dict[str, Any]
    ) -> JobTechRequirement:
        """Create new requirement or update existing one."""
        try:
            # Check if requirement already exists
            existing = self.get_by_job_and_tech(job_id, tech_id)
            
            if existing:
                # Update existing requirement
                updated = self.update(existing.requirement_id, requirement_data)
                logger.debug(f"Updated tech requirement for job {job_id}, tech {tech_id}")
                return updated
            else:
                # Create new requirement
                requirement_data.update({"job_id": job_id, "tech_id": tech_id})
                new_requirement = self.create(requirement_data)
                logger.debug(f"Created tech requirement for job {job_id}, tech {tech_id}")
                return new_requirement
                
        except Exception as e:
            logger.error(f"Error creating/updating requirement: {e}")
            raise

