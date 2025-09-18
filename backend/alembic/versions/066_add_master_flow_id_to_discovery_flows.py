"""Add master_flow_id to discovery_flows table

Revision ID: 066_add_master_flow_id_to_discovery_flows
Revises: 065_add_discovered_at_to_assets
Create Date: 2025-09-18 04:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "066_add_master_flow_id_to_discovery_flows"
down_revision = "065_add_discovered_at_to_assets"
branch_labels = None
depends_on = None


def column_exists(table_name, column_name, schema="migration"):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = :table_name
                    AND column_name = :column_name
                )
                """
            ).bindparams(schema=schema, table_name=table_name, column_name=column_name)
        ).scalar()
        return result
    except Exception as e:
        print(
            f"Error checking if column {column_name} exists in table {table_name}: {e}"
        )
        # If we get an error, assume column exists to avoid trying to create it
        return True


def upgrade():
    """Add master_flow_id column to discovery_flows table if it doesn't exist"""

    # Check if master_flow_id column already exists
    if not column_exists("discovery_flows", "master_flow_id"):
        print("Adding master_flow_id column to discovery_flows table...")

        # Add the master_flow_id column
        op.add_column(
            "discovery_flows",
            sa.Column(
                "master_flow_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
                comment="Reference to the master flow in crewai_flow_state_extensions",
            ),
            schema="migration",
        )

        # Add an index for better query performance
        op.create_index(
            "ix_discovery_flows_master_flow_id",
            "discovery_flows",
            ["master_flow_id"],
            schema="migration",
        )

        # Add foreign key constraint to crewai_flow_state_extensions
        op.create_foreign_key(
            "fk_discovery_flows_master_flow",
            "discovery_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["id"],
            source_schema="migration",
            referent_schema="migration",
            ondelete="CASCADE",
        )

        # Update existing records to link with master flows based on flow_id
        bind = op.get_bind()
        bind.execute(
            sa.text(
                """
                UPDATE migration.discovery_flows df
                SET master_flow_id = cfe.id
                FROM migration.crewai_flow_state_extensions cfe
                WHERE df.flow_id = cfe.flow_id
                AND df.client_account_id = cfe.client_account_id
                AND df.engagement_id = cfe.engagement_id
                AND df.master_flow_id IS NULL
                """
            )
        )

        print("Successfully added master_flow_id column to discovery_flows table")
    else:
        print(
            "master_flow_id column already exists in discovery_flows table, skipping..."
        )


def downgrade():
    """Remove master_flow_id column from discovery_flows table"""

    if column_exists("discovery_flows", "master_flow_id"):
        print("Removing master_flow_id column from discovery_flows table...")

        # Drop the foreign key constraint first
        op.drop_constraint(
            "fk_discovery_flows_master_flow",
            "discovery_flows",
            schema="migration",
            type_="foreignkey",
        )

        # Drop the index
        op.drop_index(
            "ix_discovery_flows_master_flow_id",
            table_name="discovery_flows",
            schema="migration",
        )

        # Drop the column
        op.drop_column("discovery_flows", "master_flow_id", schema="migration")

        print("Successfully removed master_flow_id column from discovery_flows table")
    else:
        print(
            "master_flow_id column does not exist in discovery_flows table, skipping..."
        )
