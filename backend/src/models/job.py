"""
TechInsights  - Job Model
Core model for normalized job postings from all sources
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DECIMAL, DateTime, ForeignKey,
    CheckConstraint, text, Enum as SQLEnum, ARRAY, JSON
)
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING
import enum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .data_source import DataSource
    from .company import Company
    from .job_category import JobCategory
    from .job_tech_requirement import JobTechRequirement


class ExperienceLevel(enum.Enum):
    """Experience level enumeration."""
    ENTRY = "Entry"
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"
    EXECUTIVE = "Executive"


class EmploymentType(enum.Enum):
    """Employment type enumeration."""
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    TEMPORARY = "Temporary"
    INTERNSHIP = "Internship"
    CASUAL = "Casual"


class RemoteWorkOption(enum.Enum):
    """Remote work option enumeration."""
    ON_SITE = "On-site"
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    FLEXIBLE = "Flexible"


class Job(Base, TimestampMixin):
    """Model for normalized job postings from all data sources."""
    
    __tablename__ = "jobs"
    
    # Primary key
    job_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for job posting"
    )
    
    # Source identification
    external_job_id = Column(
        String(255),
        nullable=False,
        comment="Original job ID from the source platform"
    )
    
    source_id = Column(
        Integer,
        ForeignKey("data_sources.source_id"),
        nullable=False,
        comment="Reference to data source"
    )
    
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id"),
        comment="Reference to company profile"
    )
    
    # Job details
    title = Column(
        String(500),
        nullable=False,
        comment="Job title or position name"
    )
    
    description_raw = Column(
        text,
        comment="Original HTML/formatted job description"
    )
    
    description_cleaned = Column(
        text,
        comment="Cleaned text description for analysis"
    )
    
    summary = Column(
        text,
        comment="Brief job summary (first 500 characters)"
    )
    
    # Location and work arrangement
    location = Column(
        String(255),
        comment="Job location as provided by source"
    )
    
    city = Column(
        String(100),
        comment="Normalized city name"
    )
    
    state_province = Column(
        String(100),
        comment="State or province"
    )
    
    country = Column(
        String(50),
        default="New Zealand",
        comment="Country location"
    )
    
    postal_code = Column(
        String(20),
        comment="Postal or ZIP code"
    )
    
    is_remote_friendly = Column(
        Boolean,
        default=False,
        comment="Whether remote work is supported"
    )
    
    remote_work_option = Column(
        SQLEnum(RemoteWorkOption),
        comment="Type of remote work arrangement"
    )
    
    # Compensation information
    salary_min = Column(
        DECIMAL(10, 2),
        comment="Minimum salary amount"
    )
    
    salary_max = Column(
        DECIMAL(10, 2),
        comment="Maximum salary amount"
    )
    
    salary_currency = Column(
        String(10),
        default="NZD",
        comment="Salary currency code"
    )
    
    salary_period = Column(
        String(20),
        comment="Salary period (hourly, daily, weekly, monthly, annually)"
    )
    
    salary_is_negotiable = Column(
        Boolean,
        default=False,
        comment="Whether salary is negotiable"
    )
    
    # Job classification
    experience_level = Column(
        SQLEnum(ExperienceLevel),
        comment="Required experience level"
    )
    
    employment_type = Column(
        SQLEnum(EmploymentType),
        comment="Type of employment"
    )
    
    category_id = Column(
        Integer,
        ForeignKey("job_categories.category_id"),
        comment="Job category classification"
    )
    
    seniority_level = Column(
        Integer,
        comment="Seniority level on 1-10 scale"
    )
    
    # URLs and references
    job_url = Column(
        String(1000),
        comment="Direct URL to job posting"
    )
    
    application_url = Column(
        String(1000),
        comment="URL for job application"
    )
    
    company_url = Column(
        String(1000),
        comment="Company profile URL on job platform"
    )
    
    # Dates and timing
    posted_date = Column(
        DateTime(timezone=True),
        comment="When the job was originally posted"
    )
    
    expires_date = Column(
        DateTime(timezone=True),
        comment="When the job posting expires"
    )
    
    last_seen_date = Column(
        DateTime(timezone=True),
        comment="Last time this job was seen active"
    )
    
    application_deadline = Column(
        DateTime(timezone=True),
        comment="Application deadline if specified"
    )
    
    # Data quality and processing
    collected_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="When this job was collected by our system"
    )
    
    last_updated = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Last time job data was updated"
    )
    
    processing_status = Column(
        String(20),
        default="pending",
        comment="Processing status (pending, processed, failed, archived)"
    )
    
    data_quality_score = Column(
        DECIMAL(3, 2),
        comment="Calculated data quality score (0.0-1.0)"
    )
    
    completeness_score = Column(
        DECIMAL(3, 2),
        comment="How complete the job data is (0.0-1.0)"
    )
    
    # Content analysis
    word_count = Column(
        Integer,
        comment="Word count of job description"
    )
    
    required_tech_count = Column(
        Integer,
        default=0,
        comment="Number of required technologies identified"
    )
    
    preferred_tech_count = Column(
        Integer,
        default=0,
        comment="Number of preferred technologies identified"
    )
    
    benefits_mentioned = Column(
        ARRAY(String),
        comment="Array of benefits mentioned in posting"
    )
    
    perks_mentioned = Column(
        ARRAY(String),
        comment="Array of perks mentioned in posting"
    )
    
    # Status and management
    is_active = Column(
        Boolean,
        default=True,
        comment="Whether job posting is currently active"
    )
    
    is_duplicate = Column(
        Boolean,
        default=False,
        comment="Whether this is identified as a duplicate posting"
    )
    
    duplicate_of = Column(
        Integer,
        ForeignKey("jobs.job_id"),
        comment="Reference to original job if this is a duplicate"
    )
    
    is_featured = Column(
        Boolean,
        default=False,
        comment="Whether this is a featured/premium job posting"
    )
    
    is_urgent = Column(
        Boolean,
        default=False,
        comment="Whether this is marked as urgent"
    )
    
    # Analytics and engagement
    view_count = Column(
        Integer,
        default=0,
        comment="Number of times this job has been viewed"
    )
    
    apply_count = Column(
        Integer,
        default=0,
        comment="Number of applications received (if available)"
    )
    
    # Metadata storage
    raw_data = Column(
        JSON,
        comment="Original job posting data for debugging and reprocessing"
    )
    
    extraction_metadata = Column(
        JSON,
        comment="Metadata about the extraction process"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "salary_max >= salary_min",
            name="valid_salary_range"
        ),
        CheckConstraint(
            "expires_date >= posted_date",
            name="valid_dates"
        ),
        CheckConstraint(
            "seniority_level >= 1 AND seniority_level <= 10",
            name="valid_seniority_level"
        ),
        CheckConstraint(
            "data_quality_score >= 0 AND data_quality_score <= 1",
            name="valid_data_quality_score"
        ),
        # Unique constraint for external_job_id + source_id will be added in migration
    )
    
    # Relationships
    data_source: "relationship[DataSource]" = relationship(
        "DataSource",
        back_populates="jobs"
    )
    
    company: "relationship[Company | None]" = relationship(
        "Company",
        back_populates="jobs"
    )
    
    job_category: "relationship[JobCategory | None]" = relationship(
        "JobCategory",
        back_populates="jobs"
    )
    
    tech_requirements: "relationship[list[JobTechRequirement]]" = relationship(
        "JobTechRequirement",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    
    # Self-referential relationship for duplicates
    original_job: "relationship[Job | None]" = relationship(
        "Job",
        remote_side="Job.job_id",
        back_populates="duplicate_jobs"
    )
    
    duplicate_jobs: "relationship[list[Job]]" = relationship(
        "Job",
        back_populates="original_job"
    )
    
    def __repr__(self) -> str:
        """String representation of the Job."""
        return f"<Job(id={self.job_id}, title='{self.title[:50]}...', source={self.source_id})>"
    
    @property
    def salary_range_display(self) -> str:
        """Get formatted salary range for display."""
        if self.salary_min and self.salary_max:
            if self.salary_min == self.salary_max:
                return f"{self.salary_currency} {self.salary_min:,.0f}"
            return f"{self.salary_currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        elif self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,.0f}+"
        elif self.salary_max:
            return f"Up to {self.salary_currency} {self.salary_max:,.0f}"
        return "Salary not specified"
    
    @property
    def is_recent(self) -> bool:
        """Check if job was posted within the last 7 days."""
        if not self.posted_date:
            return False
        
        from datetime import datetime, timedelta
        return self.posted_date >= datetime.now() - timedelta(days=7)
    
    @property
    def has_salary_info(self) -> bool:
        """Check if job has any salary information."""
        return self.salary_min is not None or self.salary_max is not None
    
    def update_view_count(self) -> None:
        """Increment the view count for this job."""
        if self.view_count is None:
            self.view_count = 1
        else:
            self.view_count += 1
    
    def mark_as_duplicate(self, original_job_id: int) -> None:
        """Mark this job as a duplicate of another job."""
        self.is_duplicate = True
        self.duplicate_of = original_job_id
        self.is_active = False

