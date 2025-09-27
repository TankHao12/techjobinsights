"""Add indexes for analytics performance optimization

Revision ID: add_analytics_indexes
Revises: f01697fac56a

This migration adds critical indexes to improve performance of analytics endpoints,
specifically the trending-skills query which was timing out (30+ seconds).

Key optimizations:
1. GIN index on extracted_skills JSONB column for fast skill lookup
2. Composite index on (posted_date, is_active, is_tech_job) for date filtering
3. Index on is_tech_job for fast tech job filtering

Expected improvement: 30+ seconds → <1 second for trending-skills endpoint
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_analytics_indexes'
down_revision: Union[str, None] = 'e791035c44db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN index on extracted_skills JSONB column
    # This dramatically speeds up jsonb_each() operations
    op.create_index(
        'idx_jobs_extracted_skills_gin',
        'jobs',
        ['extracted_skills'],
        unique=False,
        postgresql_using='gin'
    )
    
    # Create composite index for date + filters used in analytics queries
    # This helps with: WHERE posted_date >= X AND is_tech_job = TRUE AND is_active = TRUE
    op.create_index(
        'idx_jobs_analytics_filters',
        'jobs',
        ['posted_date', 'is_tech_job', 'is_active'],
        unique=False
    )
    
    # Create index on is_tech_job for fast filtering
    op.create_index(
        'idx_jobs_is_tech_job',
        'jobs',
        ['is_tech_job'],
        unique=False
    )
    
    # Create index on is_active for filtering active jobs
    op.create_index(
        'idx_jobs_is_active',
        'jobs',
        ['is_active'],
        unique=False
    )
    
    # Create index on posted_date for time-based queries
    op.create_index(
        'idx_jobs_posted_date',
        'jobs',
        [sa.text('posted_date DESC')],  # DESC for recent jobs first
        unique=False
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('idx_jobs_posted_date', table_name='jobs')
    op.drop_index('idx_jobs_is_active', table_name='jobs')
    op.drop_index('idx_jobs_is_tech_job', table_name='jobs')
    op.drop_index('idx_jobs_analytics_filters', table_name='jobs')
    op.drop_index('idx_jobs_extracted_skills_gin', table_name='jobs', postgresql_using='gin')
