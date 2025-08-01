"""
TechInsights  - Tech Trend Analytics Model
Model for pre-computed technology trend analytics
"""

from sqlalchemy import (
    Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey,
    CheckConstraint, text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from .base import Base
from .job import ExperienceLevel

if TYPE_CHECKING:
    from .tech_stack import TechStack
    from .data_source import DataSource


class TechTrendAnalytics(Base):
    """Model for pre-computed technology trend analytics for performance."""
    
    __tablename__ = "tech_trend_analytics"
    
    # Primary key
    trend_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for trend record"
    )
    
    tech_id = Column(
        Integer,
        ForeignKey("tech_stacks.tech_id"),
        nullable=False,
        comment="Reference to technology stack"
    )
    
    # Time period
    period_start = Column(
        Date,
        nullable=False,
        comment="Start date of analysis period"
    )
    
    period_end = Column(
        Date,
        nullable=False,
        comment="End date of analysis period"
    )
    
    period_type = Column(
        String(20),
        nullable=False,
        comment="Type of period (daily, weekly, monthly, quarterly)"
    )
    
    # Metrics
    job_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of jobs mentioning this technology"
    )
    
    total_jobs_in_period = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of jobs in the analysis period"
    )
    
    percentage = Column(
        DECIMAL(5, 2),
        nullable=False,
        default=0.00,
        comment="Percentage of jobs mentioning this technology"
    )
    
    growth_rate = Column(
        DECIMAL(5, 2),
        comment="Growth rate compared to previous period"
    )
    
    velocity = Column(
        DECIMAL(5, 2),
        comment="Rate of change in demand over time"
    )
    
    rank_position = Column(
        Integer,
        comment="Ranking within category for this period"
    )
    
    rank_change = Column(
        Integer,
        comment="Change in ranking from previous period"
    )
    
    # Filters applied
    experience_level = Column(
        SQLEnum(ExperienceLevel),
        comment="Experience level filter applied"
    )
    
    location_filter = Column(
        String(255),
        comment="Location filter applied"
    )
    
    source_filter = Column(
        Integer,
        ForeignKey("data_sources.source_id"),
        comment="Data source filter applied"
    )
    
    category_filter = Column(
        String(50),
        comment="Technology category filter applied"
    )
    
    # Statistical data
    avg_salary_min = Column(
        DECIMAL(10, 2),
        comment="Average minimum salary for jobs with this technology"
    )
    
    avg_salary_max = Column(
        DECIMAL(10, 2),
        comment="Average maximum salary for jobs with this technology"
    )
    
    median_salary = Column(
        DECIMAL(10, 2),
        comment="Median salary for jobs with this technology"
    )
    
    salary_growth_rate = Column(
        DECIMAL(5, 2),
        comment="Salary growth rate for this technology"
    )
    
    # Metadata
    calculated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="When these analytics were calculated"
    )
    
    calculation_method = Column(
        String(50),
        default="automated",
        comment="Method used to calculate these analytics"
    )
    
    data_points_used = Column(
        Integer,
        comment="Number of data points used in calculation"
    )
    
    confidence_interval = Column(
        DECIMAL(5, 2),
        comment="Statistical confidence interval for the metrics"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100",
            name="valid_percentage"
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="valid_period"
        ),
        # Complex unique constraint will be added in migration
    )
    
    # Relationships
    tech_stack: "relationship[TechStack]" = relationship(
        "TechStack",
        back_populates="trend_analytics"
    )
    
    source: "relationship[DataSource | None]" = relationship(
        "DataSource"
    )
    
    def __repr__(self) -> str:
        """String representation of the TechTrendAnalytics."""
        return (f"<TechTrendAnalytics(tech_id={self.tech_id}, period={self.period_start} to {self.period_end}, "
                f"percentage={self.percentage}%)>")

