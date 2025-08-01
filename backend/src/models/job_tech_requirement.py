"""
TechInsights  - Job Tech Requirement Model
Model for technology requirements in job postings with ML-enhanced detection
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DECIMAL, DateTime, ForeignKey,
    CheckConstraint, Enum as SQLEnum, text
)
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
import enum

from .base import Base

if TYPE_CHECKING:
    from .job import Job
    from .tech_stack import TechStack


class RequirementType(enum.Enum):
    """Technology requirement type enumeration."""
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice-to-have"
    MENTIONED = "mentioned"


class JobTechRequirement(Base):
    """Model for technology requirements in job postings with ML-enhanced detection."""
    
    __tablename__ = "job_tech_requirements"
    
    # Primary key
    requirement_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for tech requirement"
    )
    
    # Foreign keys
    job_id = Column(
        Integer,
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to job posting"
    )
    
    tech_id = Column(
        Integer,
        ForeignKey("tech_stacks.tech_id"),
        nullable=False,
        comment="Reference to technology stack"
    )
    
    # Requirement classification
    requirement_type = Column(
        SQLEnum(RequirementType),
        default=RequirementType.MENTIONED,
        comment="Type of requirement (required, preferred, nice-to-have, mentioned)"
    )
    
    confidence_score = Column(
        DECIMAL(3, 2),
        default=0.50,
        comment="ML confidence in requirement classification (0.0-1.0)"
    )
    
    # Experience requirements
    years_experience = Column(
        Integer,
        comment="Required years of experience with this technology"
    )
    
    proficiency_level = Column(
        String(20),
        comment="Required proficiency level (Beginner, Intermediate, Advanced, Expert)"
    )
    
    is_primary_skill = Column(
        Boolean,
        default=False,
        comment="Whether this is identified as a primary skill for the job"
    )
    
    # Context information
    context_snippet = Column(
        text,
        comment="Text snippet where this technology was mentioned"
    )
    
    position_in_description = Column(
        Integer,
        comment="Order of appearance in job description"
    )
    
    mention_count = Column(
        Integer,
        default=1,
        comment="Number of times this technology is mentioned"
    )
    
    # Detection metadata
    detection_method = Column(
        String(50),
        comment="Method used to detect this technology (keyword, ml_classifier, manual, pattern_match)"
    )
    
    detection_confidence = Column(
        DECIMAL(3, 2),
        comment="Confidence in the detection method (0.0-1.0)"
    )
    
    detected_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="When this requirement was detected"
    )
    
    verified_at = Column(
        DateTime(timezone=True),
        comment="When this requirement was verified"
    )
    
    verified_by = Column(
        String(100),
        comment="System or user who verified this requirement"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        comment="Whether this requirement has been manually verified"
    )
    
    # Scoring and analysis
    importance_score = Column(
        DECIMAL(3, 2),
        comment="How important this skill is for the job (0.0-1.0)"
    )
    
    market_value_score = Column(
        DECIMAL(3, 2),
        comment="Market value of this skill (0.0-1.0)"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="valid_confidence_score"
        ),
        CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="valid_detection_confidence"
        ),
        CheckConstraint(
            "importance_score >= 0 AND importance_score <= 1",
            name="valid_importance_score"
        ),
        CheckConstraint(
            "market_value_score >= 0 AND market_value_score <= 1",
            name="valid_market_value_score"
        ),
        CheckConstraint(
            "years_experience >= 0 AND years_experience <= 50",
            name="valid_years_experience"
        ),
        CheckConstraint(
            "position_in_description > 0",
            name="valid_position"
        ),
        # Unique constraint for job_id + tech_id will be added in migration
    )
    
    # Relationships
    job: "relationship[Job]" = relationship(
        "Job",
        back_populates="tech_requirements"
    )
    
    tech_stack: "relationship[TechStack]" = relationship(
        "TechStack",
        back_populates="job_requirements"
    )
    
    def __repr__(self) -> str:
        """String representation of the JobTechRequirement."""
        return (f"<JobTechRequirement(job_id={self.job_id}, tech_id={self.tech_id}, "
                f"type={self.requirement_type.value}, confidence={self.confidence_score})>")
    
    @property
    def requirement_strength(self) -> str:
        """Get human-readable requirement strength."""
        if self.requirement_type == RequirementType.REQUIRED:
            return "Required"
        elif self.requirement_type == RequirementType.PREFERRED:
            return "Preferred"
        elif self.requirement_type == RequirementType.NICE_TO_HAVE:
            return "Nice to Have"
        else:
            return "Mentioned"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this requirement has high confidence score."""
        return self.confidence_score >= 0.8
    
    @property
    def experience_description(self) -> str:
        """Get formatted experience requirement description."""
        parts = []
        
        if self.years_experience:
            if self.years_experience == 1:
                parts.append("1 year")
            else:
                parts.append(f"{self.years_experience} years")
        
        if self.proficiency_level:
            parts.append(self.proficiency_level.lower())
        
        if parts:
            return f"{' '.join(parts)} experience"
        return "Experience level not specified"
    
    def update_confidence(self, new_confidence: float, method: str) -> None:
        """Update confidence score with new detection method."""
        self.confidence_score = new_confidence
        self.detection_method = method
        self.detected_at = text("CURRENT_TIMESTAMP")
    
    def verify_requirement(self, verified_by: str) -> None:
        """Mark this requirement as manually verified."""
        self.is_verified = True
        self.verified_by = verified_by
        self.verified_at = text("CURRENT_TIMESTAMP")

