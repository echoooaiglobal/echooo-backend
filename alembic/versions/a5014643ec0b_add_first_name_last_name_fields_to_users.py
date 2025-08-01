"""add_first_name_last_name_fields_to_users

Revision ID: a5014643ec0b
Revises: fb0b8ccbdfde
Create Date: 2025-08-02 03:39:27.113337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5014643ec0b'
down_revision: Union[str, None] = 'fb0b8ccbdfde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add first_name and last_name fields to users table"""
    
    # Add first_name and last_name columns
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))
    
    # Create indexes for better performance
    op.create_index('idx_users_first_name', 'users', ['first_name'])
    op.create_index('idx_users_last_name', 'users', ['last_name'])
    op.create_index('idx_users_full_name_search', 'users', ['first_name', 'last_name'])
    
    # Update profile_image_url column length to accommodate GCS URLs
    op.alter_column('users', 'profile_image_url', 
                   existing_type=sa.String(255),
                   type_=sa.String(500),
                   existing_nullable=True)
    
    # Optional: Populate first_name and last_name from existing full_name data
    # This is a smart split that handles various name formats
    op.execute("""
        UPDATE users 
        SET 
            first_name = CASE 
                WHEN full_name IS NOT NULL AND full_name != '' THEN 
                    TRIM(SPLIT_PART(full_name, ' ', 1))
                ELSE NULL
            END,
            last_name = CASE 
                WHEN full_name IS NOT NULL AND full_name != '' THEN
                    CASE 
                        WHEN ARRAY_LENGTH(STRING_TO_ARRAY(TRIM(full_name), ' '), 1) > 1 THEN 
                            TRIM(SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1))
                        ELSE ''
                    END
                ELSE NULL
            END
        WHERE full_name IS NOT NULL AND full_name != '';
    """)
    
    # Clean up empty last_name fields (set to NULL instead of empty string)
    op.execute("""
        UPDATE users 
        SET last_name = NULL 
        WHERE last_name = '';
    """)

def downgrade():
    """Remove first_name and last_name fields from users table"""
    
    # Remove indexes first
    op.drop_index('idx_users_full_name_search', table_name='users')
    op.drop_index('idx_users_last_name', table_name='users')
    op.drop_index('idx_users_first_name', table_name='users')
    
    # Revert profile_image_url column length back to original
    op.alter_column('users', 'profile_image_url', 
                   existing_type=sa.String(500),
                   type_=sa.String(255),
                   existing_nullable=True)
    
    # Remove the new columns
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
