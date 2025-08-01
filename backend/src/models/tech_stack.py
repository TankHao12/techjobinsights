"""
TechInsights  - Tech Stack Model
Model for technology stacks and skills tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ARRAY, CheckConstraint, DateTime
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .job_tech_requirement import JobTechRequirement
    from .tech_trend_analytics import TechTrendAnalytics
    from .company_tech_profile import CompanyTechProfile


class TechStack(Base, TimestampMixin):
    """Model for comprehensive technology and skills database."""
    
    __tablename__ = "tech_stacks"
    
    # Primary key
    tech_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for technology stack"
    )
    
    # Technology identification
    technology_name = Column(
        String(100),
        nullable=False,
        comment="Official technology name"
    )
    
    normalized_name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="Standardized name for analysis and matching"
    )
    
    # Classification
    category = Column(
        String(50),
        nullable=False,
        comment="Technology category (Frontend, Backend, Database, Cloud, DevOps, Mobile, AI/ML)"
    )
    
    subcategory = Column(
        String(50),
        comment="More specific categorization within main category"
    )
    
    # Alternative names and matching
    aliases = Column(
        ARRAY(String),
        comment="Array of alternative names and common misspellings"
    )
    
    # Metrics and scoring
    popularity_score = Column(
        DECIMAL(5, 2),
        default=0.00,
        comment="Global popularity metric based on multiple factors"
    )
    
    learning_difficulty = Column(
        String(20),
        comment="Learning difficulty level (Easy, Medium, Hard)"
    )
    
    market_demand = Column(
        String(20),
        comment="Market demand level (Low, Medium, High, Very High)"
    )
    
    # Detailed information
    description = Column(
        String,
        comment="Technology description and overview"
    )
    
    official_website = Column(
        String(255),
        comment="Official technology website URL"
    )
    
    documentation_url = Column(
        String(255),
        comment="Official documentation URL"
    )
    
    # Technology type flags
    is_programming_language = Column(
        Boolean,
        default=False,
        comment="Whether this is a programming language"
    )
    
    is_framework = Column(
        Boolean,
        default=False,
        comment="Whether this is a framework or library"
    )
    
    is_tool = Column(
        Boolean,
        default=False,
        comment="Whether this is a development tool"
    )
    
    is_database = Column(
        Boolean,
        default=False,
        comment="Whether this is a database technology"
    )
    
    is_cloud_service = Column(
        Boolean,
        default=False,
        comment="Whether this is a cloud service"
    )
    
    # Version and release information
    release_year = Column(
        Integer,
        comment="Year of initial release"
    )
    
    latest_version = Column(
        String(50),
        comment="Latest stable version"
    )
    
    license_type = Column(
        String(100),
        comment="Software license type"
    )
    
    # External references
    github_url = Column(
        String(255),
        comment="GitHub repository URL"
    )
    
    stackoverflow_tag = Column(
        String(100),
        comment="Stack Overflow tag name"
    )
    
    # Statistics
    job_mentions_count = Column(
        Integer,
        default=0,
        comment="Number of job postings mentioning this technology"
    )
    
    last_updated_stats = Column(
        DateTime(timezone=True),
        comment="Last time statistics were updated"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "popularity_score >= 0 AND popularity_score <= 100",
            name="valid_popularity_score"
        ),
        CheckConstraint(
            "release_year >= 1950 AND release_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 5",
            name="valid_release_year"
        ),
    )
    
    # Relationships
    job_requirements: "relationship[list[JobTechRequirement]]" = relationship(
        "JobTechRequirement",
        back_populates="tech_stack"
    )
    
    trend_analytics: "relationship[list[TechTrendAnalytics]]" = relationship(
        "TechTrendAnalytics",
        back_populates="tech_stack"
    )
    
    company_profiles: "relationship[list[CompanyTechProfile]]" = relationship(
        "CompanyTechProfile",
        back_populates="tech_stack"
    )
    
    def __repr__(self) -> str:
        """String representation of the TechStack."""
        return f"<TechStack(id={self.tech_id}, name='{self.technology_name}', category='{self.category}')>"
    
    @property
    def display_name(self) -> str:
        """Get display name with category for UI purposes."""
        return f"{self.technology_name} ({self.category})"
    
    @property
    def type_description(self) -> str:
        """Get human-readable description of technology type."""
        types = []
        if self.is_programming_language:
            types.append("Programming Language")
        if self.is_framework:
            types.append("Framework")
        if self.is_tool:
            types.append("Tool")
        if self.is_database:
            types.append("Database")
        if self.is_cloud_service:
            types.append("Cloud Service")
        
        return ", ".join(types) if types else "Technology"
    
    def matches_name(self, search_term: str) -> bool:
        """Check if search term matches this technology name or aliases."""
        search_term_lower = search_term.lower()
        
        # Check main name
        if search_term_lower in self.technology_name.lower():
            return True
        
        # Check normalized name
        if search_term_lower in self.normalized_name.lower():
            return True
        
        # Check aliases
        if self.aliases:
            for alias in self.aliases:
                if search_term_lower in alias.lower():
                    return True
        
        return False

