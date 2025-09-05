"""Add execution_metadata to CrewAIFlowStateExtensions

Revision ID: 67da5e784e40
Revises: 053_add_assessment_transition_tracking
Create Date: 2025-09-04 15:38:57.862462

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "67da5e784e40"
down_revision = "053_add_assessment_transition_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add execution_metadata column to crewai_flow_state_extensions
    op.add_column(
        "crewai_flow_state_extensions",
        sa.Column(
            "execution_metadata",
            postgresql.JSONB,
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            comment="Metadata about the execution of the flow, including timing, agents used, and performance metrics.",
        ),
    )


def downgrade() -> None:
    # Remove execution_metadata column from crewai_flow_state_extensions
    op.drop_column("crewai_flow_state_extensions", "execution_metadata")
