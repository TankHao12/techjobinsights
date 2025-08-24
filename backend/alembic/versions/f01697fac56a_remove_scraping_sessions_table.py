"""Remove scraping_sessions table

Revision ID: f01697fac56a
Revises: 662f3a682225
Create Date: 2025-10-14 23:47:45.220761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f01697fac56a'
down_revision: Union[str, None] = '662f3a682225'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove scraping_sessions table as it's unused in the application"""
    op.drop_table('scraping_sessions')


def downgrade() -> None:
    """Recreate scraping_sessions table if needed"""
    op.create_table(
        'scraping_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_term', sa.Text(), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('end_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('jobs_collected', sa.Integer(), nullable=True),
        sa.Column('pages_scraped', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scraper_version', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
