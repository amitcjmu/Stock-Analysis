"""Add selected_application_ids column to assessment_flows table

Revision ID: 029_add_selected_application_ids
Revises: 028_add_updated_at_trigger_for_failure_journal
Create Date: 2025-08-11 17:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "029_add_selected_application_ids"
down_revision = "028_add_updated_at_trigger_for_failure_journal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add selected_application_ids column if it doesn't exist"""

    # Check if column already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'assessment_flows'
            AND column_name = 'selected_application_ids'
        """
        )
    )

    if not result.fetchone():
        # Add the column with a default empty array
        op.add_column(
            "assessment_flows",
            sa.Column(
                "selected_application_ids",
                postgresql.JSONB,
                nullable=False,
                server_default="[]",
            ),
            schema="migration",
        )

        print("✅ Added selected_application_ids column to assessment_flows table")
    else:
        print(
            "ℹ️ Column selected_application_ids already exists in assessment_flows table"
        )


def downgrade() -> None:
    """Remove selected_application_ids column"""
    op.drop_column("assessment_flows", "selected_application_ids", schema="migration")
    print("✅ Removed selected_application_ids column from assessment_flows table")
