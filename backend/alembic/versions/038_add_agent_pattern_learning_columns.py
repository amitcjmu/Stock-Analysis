"""Add missing columns for agent pattern learning

Revision ID: 038_add_agent_pattern_learning_columns
Revises: 037_add_missing_audit_log_columns
Create Date: 2025-08-29 02:55:00.000000

This migration adds missing columns to the agent_discovered_patterns table
that are required for persistent agent learning and field mapping intelligence.

These columns are defined in the AgentDiscoveredPattern model but were missing
from the database, causing approval failures when agents try to learn from
user feedback.

Columns added:
- evidence_assets: JSON array to store related asset IDs as evidence
- validation_status: String to track pattern validation status
- supporting_data: JSON to store additional context and metadata
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "038_add_agent_pattern_learning_columns"
down_revision = "037_add_missing_audit_log_columns"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to support agent learning from field mapping approvals"""

    print("🔄 Adding missing columns to agent_discovered_patterns table...")

    # Check if columns already exist to make migration idempotent
    conn = op.get_bind()

    # Check for evidence_assets column
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'agent_discovered_patterns'
        AND column_name = 'evidence_assets'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "agent_discovered_patterns",
            sa.Column(
                "evidence_assets", postgresql.JSON, nullable=True, server_default="[]"
            ),
            schema="migration",
        )
        print(
            "   ✅ Added evidence_assets column (JSON array for storing related asset IDs)"
        )
    else:
        print("   ⏭️ evidence_assets column already exists, skipping")

    # Check for validation_status column
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'agent_discovered_patterns'
        AND column_name = 'validation_status'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "agent_discovered_patterns",
            sa.Column(
                "validation_status",
                sa.String(50),
                nullable=True,
                server_default="pending",
            ),
            schema="migration",
        )
        print(
            "   ✅ Added validation_status column (String for tracking pattern validation)"
        )
    else:
        print("   ⏭️ validation_status column already exists, skipping")

    # Check for supporting_data column
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'agent_discovered_patterns'
        AND column_name = 'supporting_data'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "agent_discovered_patterns",
            sa.Column(
                "supporting_data", postgresql.JSON, nullable=True, server_default="{}"
            ),
            schema="migration",
        )
        print(
            "   ✅ Added supporting_data column (JSON for storing additional context)"
        )
    else:
        print("   ⏭️ supporting_data column already exists, skipping")

    print("✅ Migration complete - agent pattern learning columns are now available")
    print(
        "   Persistent agents can now store field mapping learnings and build intelligence!"
    )


def downgrade():
    """Remove the added columns"""

    print("🔄 Removing agent pattern learning columns...")

    # Drop columns if they exist
    conn = op.get_bind()

    for column_name in ["supporting_data", "validation_status", "evidence_assets"]:
        result = conn.execute(
            sa.text(
                f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'agent_discovered_patterns'
            AND column_name = '{column_name}'
        """
            )
        )

        if result.fetchone():
            op.drop_column("agent_discovered_patterns", column_name, schema="migration")
            print(f"   ✅ Removed {column_name} column")
        else:
            print(f"   ⏭️ {column_name} column doesn't exist, skipping")

    print("✅ Downgrade complete - agent pattern learning columns removed")
