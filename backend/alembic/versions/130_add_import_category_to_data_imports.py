"""
Add import_category and processing_config columns to data_imports.

Revision ID: 130_add_import_category_to_data_imports
Revises: 129_add_dependents_column_to_assets
Create Date: 2025-11-12

Adds support for categorising data imports and persisting per-category
processing configuration without introducing new tables.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "130_add_import_category_to_data_imports"
down_revision = "129_add_dependents_column_to_assets"
branch_labels = None
depends_on = None

IMPORT_CATEGORY_CHECK_NAME = "ck_data_imports_import_category_valid"
IMPORT_CATEGORY_INDEX_NAME = "ix_data_imports_import_category"
IMPORT_CATEGORY_VALUES = (
    "cmdb_export",
    "app_discovery",
    "infrastructure",
    "sensitive_data",
)


def upgrade() -> None:
    """Add import_category + processing_config columns with supporting index."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [
        column["name"]
        for column in inspector.get_columns("data_imports", schema="migration")
    ]

    if "import_category" not in existing_columns:
        op.add_column(
            "data_imports",
            sa.Column(
                "import_category",
                sa.String(length=50),
                nullable=True,
                comment="High-level category for routing import processing.",
            ),
            schema="migration",
        )

        allowed_values = ", ".join(f"'{value}'" for value in IMPORT_CATEGORY_VALUES)
        op.create_check_constraint(
            IMPORT_CATEGORY_CHECK_NAME,
            "data_imports",
            f"(import_category IS NULL) OR (import_category IN ({allowed_values}))",
            schema="migration",
        )

        existing_indexes = [
            idx["name"]
            for idx in inspector.get_indexes("data_imports", schema="migration")
        ]
        if IMPORT_CATEGORY_INDEX_NAME not in existing_indexes:
            op.create_index(
                IMPORT_CATEGORY_INDEX_NAME,
                "data_imports",
                ["import_category"],
                unique=False,
                schema="migration",
            )

    if "processing_config" not in existing_columns:
        op.add_column(
            "data_imports",
            sa.Column(
                "processing_config",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
                comment="Processor configuration blob scoped to import category.",
            ),
            schema="migration",
        )


def downgrade() -> None:
    """Remove processing_config and import_category columns plus related index."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_indexes = [
        idx["name"] for idx in inspector.get_indexes("data_imports", schema="migration")
    ]
    if IMPORT_CATEGORY_INDEX_NAME in existing_indexes:
        op.drop_index(
            IMPORT_CATEGORY_INDEX_NAME,
            table_name="data_imports",
            schema="migration",
        )

    constraints = [
        constraint["name"]
        for constraint in inspector.get_check_constraints(
            "data_imports", schema="migration"
        )
    ]
    if IMPORT_CATEGORY_CHECK_NAME in constraints:
        op.drop_constraint(
            IMPORT_CATEGORY_CHECK_NAME,
            "data_imports",
            type_="check",
            schema="migration",
        )

    existing_columns = [
        column["name"]
        for column in inspector.get_columns("data_imports", schema="migration")
    ]

    if "processing_config" in existing_columns:
        op.drop_column("data_imports", "processing_config", schema="migration")

    if "import_category" in existing_columns:
        op.drop_column("data_imports", "import_category", schema="migration")
