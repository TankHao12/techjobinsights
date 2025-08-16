"""
SQLAlchemy models for the jobs database tables
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, DECIMAL, ForeignKey, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from .enums import EmploymentType, ExperienceLevel, WorkArrangement

class RawJob(Base):
    """SQLAlchemy model for raw_jobs table"""
    __tablename__ = 'raw_jobs'

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    full_description = Column(Text)
    location = Column(Text)  # Raw location text from scraper
    posting_date = Column(Text) # As scraped (unparsed)
    search_term = Column(Text, nullable=False)
    scraped_at = Column(TIMESTAMP, default=datetime.utcnow)
    processing_version = Column(Text)
    processed = Column(Boolean, default=False)
    processed_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship to processed jobs
    processed_jobs = relationship("Job", back_populates="raw_job")

class Job(Base):
    """SQLAlchemy model for jobs table - processed job data"""
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    raw_job_id = Column(Integer, ForeignKey('raw_jobs.id', ondelete='CASCADE'))

    # ========================================================================
    # CORE JOB INFORMATION
    # ========================================================================
    title = Column(Text, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    description = Column(Text)
    
    # ========================================================================
    # DATES - Posted date passed directly from raw_jobs.posting_date
    # ========================================================================
    posted_date = Column(Date)  # Passed from raw_jobs, not NLP parsed
    scraped_at = Column(TIMESTAMP)

    # ========================================================================
    # NLP CLASSIFICATION RESULTS
    # ========================================================================
    is_tech_job = Column(Boolean, default=True)
    tech_confidence_score = Column(DECIMAL(3,2))

    # ========================================================================
    # JOB DETAILS (NLP Extracted) - Using Enums for 3NF
    # ========================================================================
    employment_type = Column(SQLEnum(EmploymentType), default=EmploymentType.NOT_SPECIFIED)
    experience_level = Column(SQLEnum(ExperienceLevel), nullable=True)
    work_arrangement = Column(SQLEnum(WorkArrangement), default=WorkArrangement.NOT_SPECIFIED)

    # ========================================================================
    # SKILLS - Single JSONB field for simplicity
    # Format: {"languages": ["Python", "Java"], "frameworks": ["Django", "React"]}
    # ========================================================================
    extracted_skills = Column(JSONB)  # Grouped by category

    # ========================================================================
    # SALARY INFORMATION
    # ========================================================================
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(Text, default='NZD')
    salary_period = Column(Text)  # year, month, hour
    salary_raw_text = Column(Text)  # Original salary text for reference
    salary_confidence_score = Column(DECIMAL(3,2))

    # ========================================================================
    # PROCESSING METADATA
    # ========================================================================
    processed_at = Column(TIMESTAMP, default=datetime.utcnow)
    processing_version = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    # ========================================================================
    # TRACEABILITY
    # ========================================================================
    original_url = Column(Text)
    found_via_search_term = Column(Text)

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    raw_job = relationship("RawJob", back_populates="processed_jobs")
    company = relationship("Company", back_populates="jobs")
    location = relationship("Location", back_populates="jobs")
    category = relationship("Category", back_populates="jobs")

class Company(Base):
    """
    Simplified SQLAlchemy model for companies table.
    
    Only stores company name - we can't scrape other details from job listings.
    Uses normalized_name for case-insensitive duplicate detection.
    """
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)  # Removed unique constraint - use normalized_name for uniqueness
    normalized_name = Column(Text, unique=True, nullable=False)  # For case-insensitive matching
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="company")




class Location(Base):
    """SQLAlchemy model for locations table"""
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    city = Column(Text, nullable=False)
    region = Column(Text)
    country = Column(Text, default='New Zealand')

    # Stats
    total_jobs = Column(Integer, default=0)
    avg_salary = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="location")

class Category(Base):
    """SQLAlchemy model for categories table"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    description = Column(Text)
    color_code = Column(Text)  # Hex color for UI
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="category")

class SkillTrend(Base):
    """SQLAlchemy model for skill_trends table"""
    __tablename__ = 'skill_trends'

    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    date_recorded = Column(Date, nullable=False)
    job_count = Column(Integer, default=0)
    new_jobs_count = Column(Integer, default=0)
    avg_salary = Column(DECIMAL(10, 2))
    demand_score = Column(DECIMAL(5, 2))  # Calculated metric
    growth_percentage = Column(DECIMAL(5, 2))