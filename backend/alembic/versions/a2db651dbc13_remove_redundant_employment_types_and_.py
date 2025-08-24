"""Remove redundant employment_types and experience_levels tables

Revision ID: a2db651dbc13
Revises: f01697fac56a
Create Date: 2025-10-15 00:20:09.415096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2db651dbc13'
down_revision: Union[str, None] = 'f01697fac56a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove redundant employment_types and experience_levels tables.
    
    These tables are not used - the Job model uses SQLEnum instead,
    storing values directly in the jobs table as VARCHAR columns.
    """
    op.drop_table('employment_types')
    op.drop_table('experience_levels')


def downgrade() -> None:
    """Recreate employment_types and experience_levels tables if needed"""
    # Recreate employment_types table
    op.create_table(
        'employment_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Recreate experience_levels table
    op.create_table(
        'experience_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('min_years', sa.Integer(), nullable=True),
        sa.Column('max_years', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
