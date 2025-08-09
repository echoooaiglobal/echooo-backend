"""add_archive_optimization_indexes

Revision ID: 5eb380bdcae8
Revises: a5014643ec0b
Create Date: 2025-08-09 02:51:27.162024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5eb380bdcae8'
down_revision: Union[str, None] = 'a5014643ec0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the optimized archive candidates index
    op.create_index(
        'ix_assigned_influencers_archive_candidates',
        'assigned_influencers',
        ['attempts_made', 'archived_at', 'type', 'last_contacted_at'],
        postgresql_where="attempts_made = 3 AND archived_at IS NULL AND type != 'archived' AND last_contacted_at IS NOT NULL"
    )
    
    # Add partial index for active unarchived records
    op.create_index(
        'ix_assigned_influencers_active_unarchived',
        'assigned_influencers',
        ['type', 'archived_at', 'last_contacted_at'],
        postgresql_where="archived_at IS NULL AND type = 'active'"
    )
    
    # Add index for recent contacts
    op.create_index(
        'ix_assigned_influencers_recent_contact',
        'assigned_influencers',
        ['last_contacted_at', 'attempts_made'],
        postgresql_where="last_contacted_at IS NOT NULL AND archived_at IS NULL"
    )
    
    # Add bulk update index
    op.create_index(
        'ix_assigned_influencers_bulk_update',
        'assigned_influencers',
        ['type', 'status_id', 'archived_at']
    )
    
    # Add agent performance index
    op.create_index(
        'ix_assigned_influencers_agent_performance',
        'assigned_influencers',
        ['agent_assignment_id', 'type', 'archived_at', 'responded_at']
    )
    
    # Add campaign tracking index
    op.create_index(
        'ix_assigned_influencers_campaign_tracking',
        'assigned_influencers',
        ['campaign_influencer_id', 'type', 'attempts_made', 'responded_at']
    )

def downgrade():
    # Remove indexes in reverse order
    op.drop_index('ix_assigned_influencers_campaign_tracking', 'assigned_influencers')
    op.drop_index('ix_assigned_influencers_agent_performance', 'assigned_influencers')
    op.drop_index('ix_assigned_influencers_bulk_update', 'assigned_influencers')
    op.drop_index('ix_assigned_influencers_recent_contact', 'assigned_influencers')
    op.drop_index('ix_assigned_influencers_active_unarchived', 'assigned_influencers')
    op.drop_index('ix_assigned_influencers_archive_candidates', 'assigned_influencers')
