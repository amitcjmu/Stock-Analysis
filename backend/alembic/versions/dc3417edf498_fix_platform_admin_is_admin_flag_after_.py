"""Fix platform admin is_admin flag after 022 migration

This migration fixes an issue introduced by migration 022 where the is_admin column
was added with default false for all users, including existing platform admins.

Revision ID: dc3417edf498
Revises: 023_fix_data_imports_foreign_key_constraint
Create Date: 2025-07-29 23:59:01.455356

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "dc3417edf498"
down_revision = "023_fix_data_imports_foreign_key_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Set is_admin=true for users with platform_admin role"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Update users with platform_admin role to have is_admin=true
    op.execute(
        """
        UPDATE users
        SET is_admin = true
        WHERE id IN (
            SELECT DISTINCT ur.user_id
            FROM user_roles ur
            WHERE ur.role_type = 'platform_admin'
            AND ur.is_active = true
        )
    """
    )

    print("Updated platform admin users to have is_admin=true")


def downgrade() -> None:
    """Revert is_admin flag for platform admins (not recommended)"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # This downgrade is not recommended as it would break platform admin access
    # Keeping it minimal to avoid accidental breakage
    print("Downgrade not implemented to prevent breaking platform admin access")
