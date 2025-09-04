"""Add assessment transition tracking with pgvector support

Revision ID: 053_add_assessment_transition_tracking
Revises: 052_optimize_application_indexes
Create Date: 2025-09-03 14:30:00.000000

This migration adds assessment transition tracking to collection flows,
enabling seamless handoff from collection to assessment phases.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "053_add_assessment_transition_tracking"
down_revision = "052_optimize_application_indexes"
branch_labels = None
depends_on = None


def _get_schema() -> str:
    """Get the schema from alembic configuration or environment"""
    from alembic import context

    # Get schema from alembic configuration
    alembic_config = context.config

    # Check if schema is set in alembic config
    schema = alembic_config.get_main_option("schema")
    if schema:
        return schema

    # Default to migration schema (consistent with env.py version_table_schema)
    return "migration"


def _column_exists(conn, table_name: str, column_name: str, schema: str = None) -> bool:
    """Check if column exists using information_schema pattern"""
    if schema is None:
        schema = _get_schema()

    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = :schema AND table_name = :table AND column_name = :column)"
        ),
        {"schema": schema, "table": table_name, "column": column_name},
    )
    return result.scalar()


def _constraint_exists(conn, constraint_name: str, schema: str = None) -> bool:
    """Check if constraint exists"""
    if schema is None:
        schema = _get_schema()

    result = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints "
            "WHERE table_schema = :schema AND constraint_name = :name)"
        ),
        {"schema": schema, "name": constraint_name},
    )
    return result.scalar()


def _check_pgvector_available(conn) -> bool:
    """Check if pgvector extension is available"""
    try:
        result = conn.execute(
            sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        return result.fetchone() is not None
    except Exception:
        return False


def upgrade():
    conn = op.get_bind()
    schema = _get_schema()

    # Add assessment transition tracking columns
    if not _column_exists(conn, "collection_flows", "assessment_flow_id", schema):
        op.add_column(
            "collection_flows",
            sa.Column("assessment_flow_id", UUID(as_uuid=True), nullable=True),
            schema=schema,
        )

        # Create index for foreign key performance
        op.execute(
            sa.text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_collection_flows_assessment_flow_id
                ON {schema}.collection_flows(assessment_flow_id)
            """
            )
        )

    if not _column_exists(
        conn, "collection_flows", "assessment_transition_date", schema
    ):
        op.add_column(
            "collection_flows",
            sa.Column(
                "assessment_transition_date", sa.DateTime(timezone=True), nullable=True
            ),
            schema=schema,
        )

    # Add pgvector column for gap analysis similarity if available
    if _check_pgvector_available(conn):
        if not _column_exists(
            conn, "collection_flows", "gap_analysis_embedding", schema
        ):
            # Use raw SQL for vector column since SQLAlchemy doesn't support it directly
            op.execute(
                sa.text(
                    f"""
                    ALTER TABLE {schema}.collection_flows
                    ADD COLUMN gap_analysis_embedding vector(1024)
                """
                )
            )

            # Add comment separately
            op.execute(
                sa.text(
                    f"""
                    COMMENT ON COLUMN {schema}.collection_flows.gap_analysis_embedding
                    IS 'Vector embedding for gap analysis similarity matching'
                """
                )
            )

            # Create vector similarity index
            op.execute(
                sa.text(
                    f"""
                    CREATE INDEX IF NOT EXISTS ix_collection_flows_gap_similarity
                    ON {schema}.collection_flows
                    USING ivfflat (gap_analysis_embedding vector_cosine_ops)
                    WITH (lists = 100)
                """
                )
            )

    # NOTE: assessment_ready already exists - DO NOT add again


def downgrade():
    conn = op.get_bind()
    schema = _get_schema()

    # Drop indexes first
    op.execute(
        sa.text(f"DROP INDEX IF EXISTS {schema}.ix_collection_flows_gap_similarity")
    )
    op.execute(
        sa.text(f"DROP INDEX IF EXISTS {schema}.ix_collection_flows_assessment_flow_id")
    )

    # Drop columns
    if _column_exists(conn, "collection_flows", "gap_analysis_embedding", schema):
        op.drop_column("collection_flows", "gap_analysis_embedding", schema=schema)

    if _column_exists(conn, "collection_flows", "assessment_transition_date", schema):
        op.drop_column("collection_flows", "assessment_transition_date", schema=schema)

    if _column_exists(conn, "collection_flows", "assessment_flow_id", schema):
        op.drop_column("collection_flows", "assessment_flow_id", schema=schema)
