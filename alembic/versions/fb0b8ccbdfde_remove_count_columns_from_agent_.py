"""Remove count columns from agent_assignments

Revision ID: fb0b8ccbdfde
Revises: dcdcbc2de729
Create Date: 2025-07-29 22:27:58.122673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb0b8ccbdfde'
down_revision: Union[str, None] = 'dcdcbc2de729'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# In the migration file:
def upgrade():
    op.drop_column('agent_assignments', 'assigned_influencers_count')
    op.drop_column('agent_assignments', 'completed_influencers_count') 
    op.drop_column('agent_assignments', 'pending_influencers_count')

def downgrade():
    op.add_column('agent_assignments', sa.Column('assigned_influencers_count', sa.Integer(), nullable=False, default=0))
    op.add_column('agent_assignments', sa.Column('completed_influencers_count', sa.Integer(), nullable=False, default=0))
    op.add_column('agent_assignments', sa.Column('pending_influencers_count', sa.Integer(), nullable=False, default=0))
