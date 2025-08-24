"""Remove unused remote_ok column from locations table

Revision ID: d69fe084f296
Revises: a2db651dbc13
Create Date: 2025-10-15 00:51:10.361904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd69fe084f296'
down_revision: Union[str, None] = 'a2db651dbc13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused remote_ok column from locations table.
    
    This column was never used in the application logic:
    - All values are False (default)
    - No API endpoints use it
    - Remote work is handled via work_arrangement enum in Job model
    """
    op.drop_column('locations', 'remote_ok')


def downgrade() -> None:
    """Recreate remote_ok column if needed"""
    op.add_column('locations', sa.Column('remote_ok', sa.Boolean(), nullable=True, default=False))
