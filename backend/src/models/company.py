"""
TechInsights  - Company Model
Model for company information and profiles
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, CheckConstraint, text
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .job import Job
    from .company_tech_profile import CompanyTechProfile


class Company(Base, TimestampMixin):
    """Model for company profiles aggregated from multiple sources."""
    
    __tablename__ = "companies"
    
    # Primary key
    company_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for company"
    )
    
    # Company identification
    company_name = Column(
        String(255),
        nullable=False,
        comment="Official company name"
    )
    
    normalized_name = Column(
        String(255),
        unique=True,
        comment="Standardized company name for deduplication"
    )
    
    # Company details
    company_size = Column(
        String(50),
        comment="Company size category (startup, small, medium, large, enterprise)"
    )
    
    industry = Column(
        String(100),
        comment="Primary industry sector"
    )
    
    # URLs and web presence
    website_url = Column(
        String(255),
        comment="Company website URL"
    )
    
    linkedin_url = Column(
        String(255),
        comment="Company LinkedIn profile URL"
    )
    
    # Detailed information
    description = Column(
        text,
        comment="Company description and overview"
    )
    
    logo_url = Column(
        String(255),
        comment="URL to company logo image"
    )
    
    # Location information
    location = Column(
        String(255),
        comment="Primary company location"
    )
    
    city = Column(
        String(100),
        comment="Primary city location"
    )
    
    country = Column(
        String(50),
        default="New Zealand",
        comment="Country location"
    )
    
    # Company metrics
    founded_year = Column(
        Integer,
        comment="Year the company was founded"
    )
    
    employee_count_min = Column(
        Integer,
        comment="Minimum number of employees"
    )
    
    employee_count_max = Column(
        Integer,
        comment="Maximum number of employees"
    )
    
    glassdoor_rating = Column(
        DECIMAL(2, 1),
        comment="Glassdoor company rating (1.0-5.0)"
    )
    
    # Statistics
    total_jobs_posted = Column(
        Integer,
        default=0,
        comment="Total number of jobs posted by this company"
    )
    
    # Verification status
    is_verified = Column(
        Boolean,
        default=False,
        comment="Whether company information has been manually verified"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "employee_count_max >= employee_count_min",
            name="valid_employee_count"
        ),
        CheckConstraint(
            "founded_year >= 1800 AND founded_year <= EXTRACT(YEAR FROM CURRENT_DATE)",
            name="valid_founded_year"
        ),
        CheckConstraint(
            "glassdoor_rating >= 1.0 AND glassdoor_rating <= 5.0",
            name="valid_glassdoor_rating"
        ),
    )
    
    # Relationships
    jobs: "relationship[list[Job]]" = relationship(
        "Job",
        back_populates="company"
    )
    
    tech_profiles: "relationship[list[CompanyTechProfile]]" = relationship(
        "CompanyTechProfile",
        back_populates="company"
    )
    
    def __repr__(self) -> str:
        """String representation of the Company."""
        return f"<Company(id={self.company_id}, name='{self.company_name}', verified={self.is_verified})>"
    
    @property
    def employee_count_range(self) -> str:
        """Get formatted employee count range."""
        if self.employee_count_min and self.employee_count_max:
            if self.employee_count_min == self.employee_count_max:
                return str(self.employee_count_min)
            return f"{self.employee_count_min}-{self.employee_count_max}"
        elif self.employee_count_min:
            return f"{self.employee_count_min}+"
        elif self.employee_count_max:
            return f"Up to {self.employee_count_max}"
        return "Unknown"
    
    @property
    def company_age(self) -> int | None:
        """Calculate company age in years."""
        if self.founded_year:
            from datetime import datetime
            return datetime.now().year - self.founded_year
        return None

