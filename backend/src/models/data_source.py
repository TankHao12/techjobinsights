"""
TechInsights  - Data Source Model
Model for managing job data sources (Seek, Indeed, TradeMe, etc.)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, JSON
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .job import Job
    from .job_category import JobCategory
    from .data_quality_metrics import DataQualityMetrics


class DataSource(Base, TimestampMixin):
    """Model for job data sources configuration and monitoring."""
    
    __tablename__ = "data_sources"
    
    # Primary key
    source_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for data source"
    )
    
    # Source identification
    source_name = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique source name (seek, indeed, linkedin, trademe)"
    )
    
    # Connection configuration
    base_url = Column(
        String(255),
        comment="Base URL for the data source"
    )
    
    api_endpoint = Column(
        String(255),
        comment="API endpoint for data retrieval"
    )
    
    scraping_config = Column(
        JSON,
        comment="Source-specific scraping configuration (JSON)"
    )
    
    # Rate limiting and control
    rate_limit_per_hour = Column(
        Integer,
        default=100,
        comment="Maximum requests per hour to avoid rate limiting"
    )
    
    # Status and monitoring
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this source is currently active"
    )
    
    last_scraped_at = Column(
        DateTime(timezone=True),
        comment="Last successful scraping timestamp"
    )
    
    # Statistics
    total_jobs_collected = Column(
        Integer,
        default=0,
        comment="Total number of jobs collected from this source"
    )
    
    success_rate = Column(
        DECIMAL(5, 2),
        default=0.00,
        comment="Success rate percentage for data collection"
    )
    
    # Relationships
    jobs: "relationship[list[Job]]" = relationship(
        "Job",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )
    
    job_categories: "relationship[list[JobCategory]]" = relationship(
        "JobCategory",
        back_populates="data_source"
    )
    
    data_quality_metrics: "relationship[list[DataQualityMetrics]]" = relationship(
        "DataQualityMetrics",
        back_populates="data_source"
    )
    
    def __repr__(self) -> str:
        """String representation of the DataSource."""
        return f"<DataSource(id={self.source_id}, name='{self.source_name}', active={self.is_active})>"
    
    @property
    def is_healthy(self) -> bool:
        """Check if the data source is healthy based on success rate."""
        return self.success_rate >= 80.0 if self.success_rate else False
    
    def update_statistics(self, jobs_collected: int, success_count: int, total_attempts: int) -> None:
        """Update collection statistics for this data source."""
        self.total_jobs_collected += jobs_collected
        if total_attempts > 0:
            self.success_rate = (success_count / total_attempts) * 100.0

