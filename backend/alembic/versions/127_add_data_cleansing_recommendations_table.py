"""add data cleansing recommendations table

Revision ID: 127_add_data_cleansing_recommendations_table
Revises: 126_update_alembic_version_to_new_naming
Create Date: 2025-01-XX

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "127_add_data_cleansing_recommendations_table"
down_revision: Union[str, None] = "126_update_alembic_version_to_new_naming"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str, schema: str = "migration") -> bool:
    """Check if a table exists in the database"""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table_name
            )
        """
        ).bindparams(schema=schema, table_name=table_name)
    ).scalar()
    return result


def upgrade() -> None:
    """Add data_cleansing_recommendations table for stable recommendation persistence."""

    # Check if table exists before creating
    if not table_exists("data_cleansing_recommendations"):
        op.create_table(
            "data_cleansing_recommendations",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "flow_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("discovery_flows.flow_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("priority", sa.String(20), nullable=False),
            sa.Column("impact", sa.Text(), nullable=True),
            sa.Column("effort_estimate", sa.String(100), nullable=True),
            sa.Column("fields_affected", postgresql.JSONB, nullable=True),
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="pending"
            ),
            sa.Column("action_notes", sa.Text(), nullable=True),
            sa.Column("applied_by_user_id", sa.String(255), nullable=True),
            sa.Column("applied_at", sa.Text(), nullable=True),
            sa.Column(
                "client_account_id", postgresql.UUID(as_uuid=True), nullable=False
            ),
            sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            schema="migration",
        )

        # Create indexes
        op.create_index(
            "ix_data_cleansing_recommendations_id",
            "data_cleansing_recommendations",
            ["id"],
            schema="migration",
        )
        op.create_index(
            "ix_data_cleansing_recommendations_flow_id",
            "data_cleansing_recommendations",
            ["flow_id"],
            schema="migration",
        )
        op.create_index(
            "ix_data_cleansing_recommendations_status",
            "data_cleansing_recommendations",
            ["status"],
            schema="migration",
        )
        op.create_index(
            "ix_data_cleansing_recommendations_client_account_id",
            "data_cleansing_recommendations",
            ["client_account_id"],
            schema="migration",
        )
        op.create_index(
            "ix_data_cleansing_recommendations_engagement_id",
            "data_cleansing_recommendations",
            ["engagement_id"],
            schema="migration",
        )

        # Create trigger to update updated_at timestamp
        op.execute(
            sa.text(
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
            )
        )

        op.execute(
            sa.text(
                """
                CREATE TRIGGER update_data_cleansing_recommendations_updated_at
                    BEFORE UPDATE ON migration.data_cleansing_recommendations
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """
            )
        )

        # Add comments
        op.execute(
            sa.text(
                """
                COMMENT ON TABLE migration.data_cleansing_recommendations IS
                    'Stores data cleansing recommendations with stable primary keys instead of deterministic IDs';
                COMMENT ON COLUMN migration.data_cleansing_recommendations.id IS
                    'Stable UUID primary key that does not change when recommendation content changes';
                COMMENT ON COLUMN migration.data_cleansing_recommendations.flow_id IS
                    'Foreign key to discovery flow this recommendation belongs to';
                COMMENT ON COLUMN migration.data_cleansing_recommendations.category IS
                    'Recommendation category: standardization, validation, enrichment, deduplication';
                COMMENT ON COLUMN migration.data_cleansing_recommendations.status IS
                    'Action status: pending, applied, rejected';
            """
            )
        )

        print("Created data_cleansing_recommendations table successfully")
    else:
        print("Table data_cleansing_recommendations already exists, skipping creation")


def downgrade() -> None:
    """Remove data_cleansing_recommendations table."""

    if table_exists("data_cleansing_recommendations"):
        # Drop trigger first
        op.execute(
            sa.text(
                """
                DROP TRIGGER IF EXISTS update_data_cleansing_recommendations_updated_at
                ON migration.data_cleansing_recommendations;
            """
            )
        )

        # Drop table
        op.drop_table("data_cleansing_recommendations", schema="migration")
        print("Dropped data_cleansing_recommendations table successfully")
    else:
        print("Table data_cleansing_recommendations does not exist, skipping drop")
