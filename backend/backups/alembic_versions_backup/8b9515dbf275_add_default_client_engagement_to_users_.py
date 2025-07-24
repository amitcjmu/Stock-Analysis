"""add_default_client_engagement_to_users_simple

Revision ID: 8b9515dbf275
Revises: enhanced_client_accounts
Create Date: 2025-06-27 18:15:41.125468

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8b9515dbf275"
down_revision = "enhanced_client_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add default_client_id and default_engagement_id to users table
    op.add_column(
        "users",
        sa.Column("default_client_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "default_engagement_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_users_default_client",
        "users",
        "client_accounts",
        ["default_client_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_default_engagement",
        "users",
        "engagements",
        ["default_engagement_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Remove foreign key constraints
    op.drop_constraint("fk_users_default_engagement", "users", type_="foreignkey")
    op.drop_constraint("fk_users_default_client", "users", type_="foreignkey")

    # Remove columns
    op.drop_column("users", "default_engagement_id")
    op.drop_column("users", "default_client_id")
