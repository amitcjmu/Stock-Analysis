"""
Add indexes for readiness/status fields and failure journal table

Revision ID: 027_add_indexes_and_failure_journal
Revises: 026_add_assessment_readiness_fields_to_assets
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "027_add_indexes_and_failure_journal"
down_revision = "026_add_assessment_readiness_fields_to_assets"
branch_labels = None
depends_on = None


def _get_target_schema(inspector: Inspector) -> str:
    """Return the application schema; prefer 'migration' but fall back to default."""
    try:
        schemas = inspector.get_schema_names()
    except Exception:
        schemas = []
    if "migration" in schemas:
        return "migration"
    return inspector.default_schema_name or "public"


def _index_exists(
    inspector: Inspector, table: str, index_name: str, schema: str
) -> bool:
    try:
        idx = inspector.get_indexes(table, schema=schema)
        return any(i.get("name") == index_name for i in idx)
    except Exception:
        return False


def _table_exists(inspector: Inspector, table: str, schema: str) -> bool:
    try:
        return inspector.has_table(table, schema=schema)
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = _get_target_schema(inspector)

    # Guard: only touch indexes if assets table exists
    if _table_exists(inspector, "assets", schema):
        if not _index_exists(
            inspector, "assets", "ix_assets_client_engagement_readiness", schema
        ):
            op.create_index(
                "ix_assets_client_engagement_readiness",
                "assets",
                ["client_account_id", "engagement_id", "assessment_readiness"],
                unique=False,
                schema=schema,
            )

        if not _index_exists(inspector, "assets", "ix_assets_discovery_status", schema):
            op.create_index(
                "ix_assets_discovery_status",
                "assets",
                ["discovery_status"],
                unique=False,
                schema=schema,
            )

    # Failure journal table (idempotent)
    if not _table_exists(inspector, "failure_journal", schema):
        op.create_table(
            "failure_journal",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "client_account_id", postgresql.UUID(as_uuid=True), nullable=False
            ),
            sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column("operation", sa.String(length=128), nullable=False),
            sa.Column(
                "payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("trace", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            schema=schema,
        )

    # Create failure journal index if missing
    if _table_exists(inspector, "failure_journal", schema) and not _index_exists(
        inspector, "failure_journal", "ix_failure_journal_engagement_op", schema
    ):
        op.create_index(
            "ix_failure_journal_engagement_op",
            "failure_journal",
            ["engagement_id", "operation"],
            unique=False,
            schema=schema,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = _get_target_schema(inspector)

    # Drop failure journal artifacts if present
    try:
        op.drop_index(
            "ix_failure_journal_engagement_op",
            table_name="failure_journal",
            schema=schema,
        )
    except Exception:
        pass
    try:
        op.drop_table("failure_journal", schema=schema)
    except Exception:
        pass

    # Drop indexes from assets if they exist
    try:
        op.drop_index("ix_assets_discovery_status", table_name="assets", schema=schema)
    except Exception:
        pass
    try:
        op.drop_index(
            "ix_assets_client_engagement_readiness",
            table_name="assets",
            schema=schema,
        )
    except Exception:
        pass
