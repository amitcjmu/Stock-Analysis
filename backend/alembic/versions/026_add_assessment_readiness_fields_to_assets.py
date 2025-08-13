"""Add discovery/assessment readiness fields to assets

Revision ID: 026_add_assessment_readiness_fields_to_assets
Revises: 025_migrate_8r_to_5r_strategies
Create Date: 2025-08-08
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "026_add_assessment_readiness_fields_to_assets"
down_revision = "025_migrate_8r_to_5r_strategies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Always use 'migration' schema
    inspector = sa.inspect(conn)
    schema = "migration"

    def _column_exists(table: str, column: str) -> bool:
        try:
            cols = inspector.get_columns(table, schema=schema)
            return any(col.get("name") == column for col in cols)
        except Exception:
            return False

    # Add columns if missing
    if not _column_exists("assets", "discovery_status"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'discovery_status'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column("discovery_status", sa.VARCHAR(length=50), nullable=True),
                schema=schema,
            )
        op.create_index(
            op.f("ix_assets_discovery_status"),
            "assets",
            ["discovery_status"],
            unique=False,
            schema=schema,
        )

    if not _column_exists("assets", "discovery_completed_at"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'discovery_completed_at'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column(
                    "discovery_completed_at", sa.TIMESTAMP(timezone=True), nullable=True
                ),
                schema=schema,
            )

    if not _column_exists("assets", "assessment_readiness"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'assessment_readiness'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column(
                    "assessment_readiness",
                    sa.VARCHAR(length=50),
                    nullable=True,
                    server_default=sa.text("'not_ready'"),
                ),
                schema=schema,
            )
        op.create_index(
            op.f("ix_assets_assessment_readiness"),
            "assets",
            ["assessment_readiness"],
            unique=False,
            schema=schema,
        )

    if not _column_exists("assets", "assessment_readiness_score"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'assessment_readiness_score'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column("assessment_readiness_score", sa.Float(), nullable=True),
                schema=schema,
            )

    if not _column_exists("assets", "assessment_blockers"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'assessment_blockers'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column("assessment_blockers", sa.JSON(), nullable=True),
                schema=schema,
            )

    if not _column_exists("assets", "assessment_recommendations"):
        # Check if column already exists

        conn = op.get_bind()

        result = conn.execute(
            sa.text(
                """

            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'migration'

            AND table_name = 'assets'

            AND column_name = 'assessment_recommendations'

        """
            )
        )

        if not result.fetchone():

            op.add_column(
                "assets",
                sa.Column("assessment_recommendations", sa.JSON(), nullable=True),
                schema=schema,
            )


def downgrade() -> None:
    """Best-effort drop of readiness-related columns/indexes."""
    # bind = op.get_bind()  # Commented out - not used
    # insp = sa.inspect(bind)  # Commented out - not used
    schema = "migration"

    # Helper functions to keep complexity low
    def _drop_index(idx: str) -> None:
        try:
            op.drop_index(op.f(idx), table_name="assets", schema=schema)
        except Exception:
            pass

    def _drop_col(col: str) -> None:
        try:
            op.drop_column("assets", col, schema=schema)
        except Exception:
            pass

    for col in [
        "assessment_recommendations",
        "assessment_blockers",
        "assessment_readiness_score",
    ]:
        _drop_col(col)

    _drop_index("ix_assets_assessment_readiness")
    _drop_col("assessment_readiness")
    _drop_col("discovery_completed_at")
    _drop_index("ix_assets_discovery_status")
    _drop_col("discovery_status")
