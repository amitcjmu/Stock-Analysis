"""ensure_user_profiles_exist

Revision ID: ensure_user_profiles
Revises: 
Create Date: 2025-01-02

This is a TEMPLATE migration showing how to use migration hooks.
Copy this pattern when creating new migrations that might affect users.
"""
from alembic import op
import sqlalchemy as sa

# Import our migration hooks
from app.core.migration_hooks import MigrationHooks

# revision identifiers, used by Alembic.
revision = 'ensure_user_profiles'
down_revision = None  # Set this to your actual previous migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply your schema changes here, then run hooks to ensure data consistency.
    """
    
    # Example: Add a new column to users table
    # op.add_column('users', sa.Column('new_field', sa.String(100)))
    
    # IMPORTANT: After any user-related schema changes, run the hooks
    # This ensures all users have profiles and platform admin exists
    MigrationHooks.run_all_hooks(op)
    
    # Or run specific hooks:
    # MigrationHooks.ensure_user_profiles_sync(op)
    # MigrationHooks.ensure_platform_admin_sync(op)
    # MigrationHooks.cleanup_invalid_demo_admins_sync(op)


def downgrade():
    """
    Reverse the schema changes.
    Note: We don't reverse the data consistency fixes.
    """
    
    # Example: Remove the column
    # op.drop_column('users', 'new_field')
    
    pass