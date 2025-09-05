"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.models import EmploymentType, ExperienceLevel, SkillCategory, SkillType, ProficiencyLevel

# =============================================================================
# BASE SCHEMAS
# =============================================================================

class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaginationParams(BaseModel):
    """Common pagination parameters"""
    offset: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of records to return")

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int = Field(description="Current page number")
    pages: int = Field(description="Total number of pages")
    per_page: int = Field(description="Items per page")
    has_next: bool
    has_prev: bool

# =============================================================================
# COMPANY SCHEMAS
# =============================================================================

class CompanyBase(BaseModel):
    """
    Simplified company schema.
    Only stores company name - we can't scrape other details from job listings.
    """
    name: str = Field(..., max_length=255, description="Company name as shown in job listings")

class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass

class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = Field(None, max_length=255)

class Company(CompanyBase):
    """Complete company schema"""
    id: int
    normalized_name: str = Field(..., description="Normalized company name for deduplication")
    created_at: datetime = Field(..., description="When company was first seen")
    
    class Config:
        from_attributes = True

class CompanyWithStats(Company):
    """Company with job statistics"""
    active_jobs_count: int = Field(0, description="Number of currently active job postings")
    total_jobs_count: int = Field(0, description="Total jobs posted by this company")

# =============================================================================
# LOCATION SCHEMAS
# =============================================================================

class LocationBase(BaseModel):
    """Base location schema"""
    city: str = Field(..., max_length=100, description="City name")
    region: Optional[str] = Field(None, max_length=100, description="Region name")
    country: str = Field(default="New Zealand", max_length=100)
    latitude: Optional[Decimal] = Field(None, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, description="Longitude coordinate")
    timezone: str = Field(default="Pacific/Auckland", max_length=50)

class LocationCreate(LocationBase):
    """Schema for creating a location"""
    pass

class Location(LocationBase):
    """Complete location schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# =============================================================================
# CATEGORY SCHEMAS
# =============================================================================

class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color_code: Optional[str] = Field(None, max_length=7, description="Hex color code")
    sort_order: int = Field(default=0, description="Display sort order")

class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass

class Category(CategoryBase):
    """Complete category schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# =============================================================================
# SKILL SCHEMAS
# =============================================================================

class SkillBase(BaseModel):
    """Base skill schema"""
    name: str = Field(..., max_length=100, description="Skill name")
    category: Optional[SkillCategory] = Field(None, description="Skill category")
    aliases: Optional[str] = Field(None, description="JSON array of alternative names")
    description: Optional[str] = Field(None, description="Skill description")
    skill_type: SkillType = Field(default=SkillType.TECHNICAL, description="Type of skill")

class SkillCreate(SkillBase):
    """Schema for creating a skill"""
    pass

class SkillUpdate(BaseModel):
    """Schema for updating a skill"""
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[SkillCategory] = None
    aliases: Optional[str] = None
    description: Optional[str] = None
    skill_type: Optional[SkillType] = None

class Skill(SkillBase, TimestampMixin):
    """Complete skill schema"""
    id: int
    popularity_score: int = 0
    
    class Config:
        from_attributes = True

class SkillWithStats(Skill):
    """Skill with job statistics"""
    job_count: int = 0
    required_count: int = 0
    primary_count: int = 0
    avg_salary: Optional[float] = None
    trend_percentage: Optional[float] = None

# =============================================================================
# JOB SCHEMAS
# =============================================================================

class JobBase(BaseModel):
    """Base job schema"""
    title: str = Field(..., max_length=500, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary in NZD")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary in NZD")
    currency: str = Field(default="NZD", max_length=3)
    employment_type: Optional[EmploymentType] = Field(None, description="Type of employment")
    experience_level: Optional[ExperienceLevel] = Field(None, description="Required experience level")
    source_url: Optional[str] = Field(None, max_length=1000, description="Original posting URL")
    source_id: Optional[str] = Field(None, max_length=100, description="External system ID")
    posted_date: Optional[date] = Field(None, description="Date job was posted")
    closing_date: Optional[date] = Field(None, description="Application closing date")
    is_active: bool = Field(default=True, description="Whether job is active")
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v

class JobCreate(JobBase):
    """Schema for creating a job"""
    company_id: int = Field(..., description="Company ID")
    location_id: Optional[int] = Field(None, description="Location ID")
    category_id: Optional[int] = Field(None, description="Category ID")

class JobUpdate(BaseModel):
    """Schema for updating a job"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[EmploymentType] = None
    experience_level: Optional[ExperienceLevel] = None
    closing_date: Optional[date] = None
    is_active: Optional[bool] = None

class Job(JobBase, TimestampMixin):
    """Complete job schema"""
    id: int
    company_id: Optional[int] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None
    scraped_at: datetime
    
    class Config:
        from_attributes = True

class JobDetail(Job):
    """Detailed job with related information"""
    company: Optional[Company] = None
    location: Optional[Location] = None
    category: Optional[Category] = None
    skills: List[Skill] = []

class JobSkillBase(BaseModel):
    """Base job skill relationship schema"""
    is_required: bool = Field(default=True, description="Whether skill is required")
    years_required: Optional[int] = Field(None, ge=0, description="Years of experience required")
    proficiency_level: Optional[ProficiencyLevel] = Field(None, description="Required proficiency level")
    is_primary: bool = Field(default=False, description="Whether this is a primary skill")

class JobSkillCreate(JobSkillBase):
    """Schema for creating job-skill relationship"""
    job_id: int
    skill_id: int

class JobSkill(JobSkillBase):
    """Complete job skill relationship"""
    job_id: int
    skill_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# =============================================================================
# ANALYTICS SCHEMAS
# =============================================================================

class SkillTrendBase(BaseModel):
    """Base skill trend schema"""
    date_recorded: date
    job_count: int = Field(ge=0, description="Total jobs requiring this skill")
    new_jobs_count: int = Field(default=0, ge=0, description="New jobs posted")
    avg_salary: Optional[Decimal] = Field(None, description="Average salary for this skill")
    demand_score: Optional[Decimal] = Field(None, description="Calculated demand score")
    growth_percentage: Optional[Decimal] = Field(None, description="Growth percentage")

class SkillTrend(SkillTrendBase):
    """Complete skill trend schema"""
    id: int
    skill_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SalaryTrendBase(BaseModel):
    """Base salary trend schema"""
    date_recorded: date
    experience_level: Optional[ExperienceLevel] = None
    avg_salary: Optional[Decimal] = None
    median_salary: Optional[Decimal] = None
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    sample_size: Optional[int] = Field(None, gt=0)

class SalaryTrend(SalaryTrendBase):
    """Complete salary trend schema"""
    id: int
    category_id: int
    location_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# =============================================================================
# SEARCH AND FILTER SCHEMAS
# =============================================================================

class JobSearchParams(PaginationParams):
    """Job search parameters"""
    query: Optional[str] = Field(None, description="Search query for title/description")
    company_id: Optional[int] = Field(None, description="Filter by company")
    location_id: Optional[int] = Field(None, description="Filter by location")
    category_id: Optional[int] = Field(None, description="Filter by category")
    skills: Optional[List[str]] = Field(None, description="Required skills")
    exclude_skills: Optional[List[str]] = Field(None, description="Skills to exclude")
    companies: Optional[List[str]] = Field(None, description="Include specific companies")
    exclude_companies: Optional[List[str]] = Field(None, description="Companies to exclude")
    employment_type: Optional[EmploymentType] = Field(None, description="Employment type")
    experience_level: Optional[ExperienceLevel] = Field(None, description="Experience level")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    location: Optional[str] = Field(None, description="Location filter (city/region)")
    remote_type: Optional[str] = Field(None, description="Remote work type (remote, onsite, hybrid)")
    posted_after: Optional[date] = Field(None, description="Posted after date")
    is_active: Optional[bool] = Field(True, description="Only active jobs")

class SkillSearchParams(PaginationParams):
    """Skill search parameters"""
    query: Optional[str] = Field(None, description="Search query for skill name")
    category: Optional[SkillCategory] = Field(None, description="Filter by category")
    skill_type: Optional[SkillType] = Field(None, description="Filter by type")
    min_job_count: Optional[int] = Field(None, ge=0, description="Minimum job count")

# =============================================================================
# DASHBOARD SCHEMAS
# =============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_jobs: int = 0
    active_jobs: int = 0
    total_companies: int = 0
    hiring_companies: int = 0
    total_skills: int = 0
    new_jobs_today: int = 0
    avg_salary: Optional[float] = None
    last_updated: datetime

class TrendingSkill(BaseModel):
    """Trending skill summary"""
    skill_id: int
    name: str
    category: Optional[SkillCategory] = None
    job_count: int
    growth_percentage: Optional[float] = None
    avg_salary: Optional[float] = None

class PopularCompany(BaseModel):
    """Popular company summary"""
    company_id: int
    name: str
    active_jobs: int
    new_jobs_this_week: int

class SkillDetail(BaseModel):
    """Detailed skill information"""
    name: str
    category: str
    current_demand: Dict[str, Any]
    growth_rate: float
    trend_data: List[Dict[str, Any]]
    top_companies: List[Dict[str, Any]]
    related_skills: List[Dict[str, Any]]
    experience_distribution: Dict[str, Any]
    location_breakdown: List[Dict[str, Any]]

class SkillComparison(BaseModel):
    """Skill comparison data"""
    skill: str
    demand: int
    growth_rate: float
    companies_using: int
    percentage: float
    trend_data: List[Dict[str, Any]]

class SkillPair(BaseModel):
    """Skill pair co-occurrence data"""
    skill1: str
    skill2: str
    job_count: int
    percentage: float
    strength: str

# =============================================================================
# API RESPONSE SCHEMAS
# =============================================================================

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# =============================================================================
# OPERATIONAL SCHEMAS
# =============================================================================
