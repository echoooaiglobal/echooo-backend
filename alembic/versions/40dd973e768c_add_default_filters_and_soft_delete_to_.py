"""Add default_filters and soft delete to campaigns

Revision ID: 40dd973e768c (add_campaign_fields)
Revises: 
Create Date: 2025-06-24 04:30:35.700257

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_campaign_fields'
down_revision: Union[str, None] = None  # Changed from 'bc2117d0de9d' to None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default_filters and soft delete fields to campaigns table only"""
    
    # Add default_filters field
    op.add_column('campaigns', 
        sa.Column('default_filters', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    
    # Add soft delete fields
    op.add_column('campaigns', 
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    
    op.add_column('campaigns', 
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    op.add_column('campaigns', 
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint for deleted_by
    op.create_foreign_key(
        'fk_campaigns_deleted_by_users', 
        'campaigns', 
        'users', 
        ['deleted_by'], 
        ['id'], 
        ondelete='SET NULL'
    )
    
    # Add index for soft delete queries (improves performance)
    op.create_index('idx_campaigns_is_deleted', 'campaigns', ['is_deleted'])

def downgrade() -> None:
    """Remove default_filters and soft delete fields from campaigns table"""
    
    # Drop index
    op.drop_index('idx_campaigns_is_deleted', table_name='campaigns')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_campaigns_deleted_by_users', 'campaigns', type_='foreignkey')
    
    # Drop columns (in reverse order)
    op.drop_column('campaigns', 'deleted_by')
    op.drop_column('campaigns', 'deleted_at')
    op.drop_column('campaigns', 'is_deleted')
    op.drop_column('campaigns', 'default_filters')