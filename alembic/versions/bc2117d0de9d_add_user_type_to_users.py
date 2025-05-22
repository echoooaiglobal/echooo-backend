"""add_user_type_to_users

Revision ID: bc2117d0de9d
Revises: 
Create Date: 2025-05-15 18:54:51.992559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc2117d0de9d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add user_type column
    op.add_column('users', sa.Column('user_type', sa.String(20), nullable=True))
    
    # Optional: Update existing users based on their roles
    # This is complex and may need adjustment based on your existing data
    op.execute("""
    UPDATE users 
    SET user_type = 
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM user_roles ur 
                JOIN roles r ON ur.role_id = r.id 
                WHERE ur.user_id = users.id AND r.name LIKE 'platform_%'
            ) THEN 'platform'
            WHEN EXISTS (
                SELECT 1 FROM user_roles ur 
                JOIN roles r ON ur.role_id = r.id 
                WHERE ur.user_id = users.id AND r.name LIKE 'company_%'
            ) THEN 'company'
            WHEN EXISTS (
                SELECT 1 FROM user_roles ur 
                JOIN roles r ON ur.role_id = r.id 
                WHERE ur.user_id = users.id AND r.name IN ('influencer', 'influencer_manager')
            ) THEN 'influencer'
            ELSE NULL
        END
    """)


def downgrade():
    # Remove user_type column
    op.drop_column('users', 'user_type')
