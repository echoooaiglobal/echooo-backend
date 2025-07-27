"""add_currency_column_and_indexes_to_campaign_influencers

Revision ID: dcdcbc2de729
Revises: 
Create Date: 2025-07-24 14:35:06.963420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcdcbc2de729'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add currency column
    op.add_column('campaign_influencers', 
                  sa.Column('currency', sa.String(length=3), nullable=True, default='USD'))
    
    # Add indexes
    op.create_index('ix_campaign_influencers_price_currency', 
                    'campaign_influencers', 
                    ['collaboration_price', 'currency'])
    
    op.create_index('ix_campaign_influencers_currency', 
                    'campaign_influencers', 
                    ['currency'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_campaign_influencers_currency')
    op.drop_index('ix_campaign_influencers_price_currency')
    
    # Drop column
    op.drop_column('campaign_influencers', 'currency')
