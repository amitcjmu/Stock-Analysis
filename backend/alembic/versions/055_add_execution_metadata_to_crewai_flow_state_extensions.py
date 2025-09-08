"""Add execution_metadata to CrewAIFlowStateExtensions

Revision ID: 055_add_execution_metadata_to_crewai_flow_state_extensions
Revises: 054_change_pattern_type_to_string
Create Date: 2025-09-04 15:38:57.862462

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "055_add_execution_metadata_to_crewai_flow_state_extensions"
down_revision = "054_change_pattern_type_to_string"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if column already exists to make migration idempotent
    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'migration' "
            "AND table_name = 'crewai_flow_state_extensions' "
            "AND column_name = 'execution_metadata')"
        )
    )

    if not result.scalar():
        # Add execution_metadata column to crewai_flow_state_extensions
        op.add_column(
            "crewai_flow_state_extensions",
            sa.Column(
                "execution_metadata",
                postgresql.JSONB,
                nullable=True,
                server_default=sa.text("'{}'::jsonb"),
                comment="Metadata about the execution of the flow, including timing, "
                "agents used, and performance metrics.",
            ),
        )


def downgrade() -> None:
    # Remove execution_metadata column from crewai_flow_state_extensions
    op.drop_column("crewai_flow_state_extensions", "execution_metadata")
