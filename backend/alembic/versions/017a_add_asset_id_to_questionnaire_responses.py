"""Add asset_id foreign key to collection_questionnaire_responses for proper asset-questionnaire linking

Revision ID: 017a_add_asset_id_to_questionnaire_responses
Revises: 016_add_security_constraints
Create Date: 2025-08-27 14:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017a_add_asset_id_to_questionnaire_responses"
down_revision: Union[str, None] = "016_add_security_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add asset_id foreign key to collection_questionnaire_responses table.

    This creates proper linkage between questionnaire responses and specific assets
    within the client/engagement context, enabling:
    - Direct asset-to-response relationships
    - Proper multi-tenant data organization
    - Application name pre-filling from asset inventory
    """
    # Add asset_id column to collection_questionnaire_responses
    op.add_column(
        "collection_questionnaire_responses",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("migration.assets.id", ondelete="CASCADE"),
            nullable=True,  # Allow null for legacy responses
            comment="Foreign key to the asset this questionnaire response is about",
        ),
        schema="migration",
    )

    # Add index for performance
    op.create_index(
        "ix_collection_questionnaire_responses_asset_id",
        "collection_questionnaire_responses",
        ["asset_id"],
        schema="migration",
    )

    # Add compound index for efficient queries by flow and asset
    op.create_index(
        "ix_collection_questionnaire_responses_flow_asset",
        "collection_questionnaire_responses",
        ["collection_flow_id", "asset_id"],
        schema="migration",
    )


def downgrade() -> None:
    """Remove asset_id foreign key from collection_questionnaire_responses table."""
    # Drop indexes first
    op.drop_index(
        "ix_collection_questionnaire_responses_flow_asset",
        table_name="collection_questionnaire_responses",
        schema="migration",
    )

    op.drop_index(
        "ix_collection_questionnaire_responses_asset_id",
        table_name="collection_questionnaire_responses",
        schema="migration",
    )

    # Drop the column
    op.drop_column("collection_questionnaire_responses", "asset_id", schema="migration")
