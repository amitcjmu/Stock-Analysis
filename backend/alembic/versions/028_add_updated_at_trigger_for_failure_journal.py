"""
Add updated_at auto-update trigger for failure_journal

Revision ID: 028_add_updated_at_trigger_for_failure_journal
Revises: 027_add_indexes_and_failure_journal
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "028_add_updated_at_trigger_for_failure_journal"
down_revision = "027_add_indexes_and_failure_journal"
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
    return "migration"  # Always default to migration schema


def _table_exists(inspector: Inspector, table: str, schema: str) -> bool:
    try:
        return inspector.has_table(table, schema=schema)
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = _get_target_schema(inspector)

    # Only proceed if table exists
    if not _table_exists(inspector, "failure_journal", schema):
        return

    # Create or replace the timestamp function (idempotent)
    op.execute(
        sa.text(
            f"""
            CREATE OR REPLACE FUNCTION "{schema}".set_timestamp()
            RETURNS trigger AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    # Recreate trigger idempotently
    op.execute(
        sa.text(
            f"""
            DROP TRIGGER IF EXISTS set_timestamp_on_failure_journal ON "{schema}".failure_journal;
            CREATE TRIGGER set_timestamp_on_failure_journal
            BEFORE UPDATE ON "{schema}".failure_journal
            FOR EACH ROW
            EXECUTE PROCEDURE "{schema}".set_timestamp();
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    schema = _get_target_schema(inspector)

    if not _table_exists(inspector, "failure_journal", schema):
        return

    # Drop trigger (keep the function as it may be referenced elsewhere)
    op.execute(
        sa.text(
            f"""
            DROP TRIGGER IF EXISTS set_timestamp_on_failure_journal ON {schema}.failure_journal;
            """
        )
    )
