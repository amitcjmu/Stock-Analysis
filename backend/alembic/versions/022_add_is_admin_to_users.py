"""Add is_admin column to users table

Revision ID: 022_add_is_admin_to_users
Revises: 021_fix_import_field_mappings_id_default
Create Date: 2025-07-28

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "022_add_is_admin_to_users"
down_revision = "021_fix_import_field_mappings_id_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_admin column to users table"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if column already exists to make migration idempotent
    result = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'users'
            AND column_name = 'is_admin'
        )
    """
            )
        )
        .scalar()
    )

    if not result:
        # Add is_admin column with default value of false
        op.add_column(
            "users",
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
            schema="migration",
        )

        # Update existing platform admin users to have is_admin=true
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

        print("Added is_admin column to users table and updated platform admins")
    else:
        print("is_admin column already exists in users table")


def downgrade() -> None:
    """Remove is_admin column from users table"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if column exists before trying to drop it
    result = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'users'
            AND column_name = 'is_admin'
        )
    """
            )
        )
        .scalar()
    )

    if result:
        op.drop_column("users", "is_admin", schema="migration")
        print("Removed is_admin column from users table")
    else:
        print("is_admin column does not exist in users table")
