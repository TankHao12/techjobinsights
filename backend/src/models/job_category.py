"""
TechInsights  - Job Category Model
Model for hierarchical job categorization from various sources
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .data_source import DataSource
    from .job import Job


class JobCategory(Base, TimestampMixin):
    """Model for hierarchical job categorization from various sources."""
    
    __tablename__ = "job_categories"
    
    # Primary key
    category_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for job category"
    )
    
    # Category information
    category_name = Column(
        String(100),
        nullable=False,
        comment="Display name of the job category"
    )
    
    # Hierarchy support
    parent_category_id = Column(
        Integer,
        ForeignKey("job_categories.category_id"),
        comment="Parent category for hierarchical structure"
    )
    
    # Source association
    source_id = Column(
        Integer,
        ForeignKey("data_sources.source_id"),
        comment="Data source this category belongs to"
    )
    
    external_category_id = Column(
        String(50),
        comment="Original category ID from the source platform"
    )
    
    # Additional information
    description = Column(
        String,
        comment="Detailed description of the job category"
    )
    
    is_tech_related = Column(
        Boolean,
        default=True,
        comment="Whether this category is technology-related"
    )
    
    # Statistics
    job_count = Column(
        Integer,
        default=0,
        comment="Number of active jobs in this category"
    )
    
    # Constraints
    __table_args__ = (
        # Unique category per source
        {"schema": None},  # Placeholder for unique constraint in migration
    )
    
    # Relationships
    data_source: "relationship[DataSource]" = relationship(
        "DataSource",
        back_populates="job_categories"
    )
    
    # Self-referential relationship for hierarchy
    parent_category: "relationship[JobCategory | None]" = relationship(
        "JobCategory",
        remote_side="JobCategory.category_id",
        back_populates="subcategories"
    )
    
    subcategories: "relationship[list[JobCategory]]" = relationship(
        "JobCategory",
        back_populates="parent_category"
    )
    
    jobs: "relationship[list[Job]]" = relationship(
        "Job",
        back_populates="job_category"
    )
    
    def __repr__(self) -> str:
        """String representation of the JobCategory."""
        return f"<JobCategory(id={self.category_id}, name='{self.category_name}', tech_related={self.is_tech_related})>"
    
    @property
    def full_category_path(self) -> str:
        """Get the full hierarchical path of this category."""
        path_parts = [self.category_name]
        current = self.parent_category
        
        while current:
            path_parts.insert(0, current.category_name)
            current = current.parent_category
        
        return " > ".join(path_parts)
    
    @property
    def is_root_category(self) -> bool:
        """Check if this is a root-level category."""
        return self.parent_category_id is None
    
    @property
    def has_subcategories(self) -> bool:
        """Check if this category has subcategories."""
        return len(self.subcategories) > 0
    
    def get_all_descendant_ids(self) -> list[int]:
        """Get all descendant category IDs recursively."""
        descendant_ids = []
        
        for subcategory in self.subcategories:
            descendant_ids.append(subcategory.category_id)
            descendant_ids.extend(subcategory.get_all_descendant_ids())
        
        return descendant_ids
    
    def update_job_count(self, count: int) -> None:
        """Update the job count for this category."""
        self.job_count = count

