"""make_hashed_password_nullable_for_oauth

Revision ID: b0b51413a3c7
Revises: add_campaign_fields
Create Date: 2025-06-30 23:21:29.016381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0b51413a3c7'
down_revision: Union[str, None] = 'add_campaign_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable to support OAuth users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=True)

def downgrade() -> None:
    # Revert back to not nullable (be careful with this!)
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=False)
