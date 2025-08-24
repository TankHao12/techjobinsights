"""Remove unused skills and job_skills tables

Revision ID: e791035c44db
Revises: d69fe084f296
Create Date: 2025-10-15 01:23:56.100474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e791035c44db'
down_revision: Union[str, None] = 'd69fe084f296'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused skills and job_skills tables.
    
    These tables were never populated by the NLP pipeline:
    - skills table: 47 seed records, never used in processing
    - job_skills table: 0 records, completely unused
    - skill_trends table: 0 records, depends on skills table
    
    Skills are stored in jobs.extracted_skills JSONB column instead.
    """
    # Drop dependent tables first (have foreign keys to skills)
    op.drop_table('skill_trends')
    op.drop_table('job_skills')
    
    # Drop skills table last
    op.drop_table('skills')


def downgrade() -> None:
    """Recreate skills and job_skills tables if needed"""
    # Recreate skills table
    op.create_table('skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('subcategory', sa.Text(), nullable=True),
        sa.Column('popularity_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Recreate job_skills junction table
    op.create_table('job_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('skill_id', sa.Integer(), nullable=True),
        sa.Column('skill_type', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
