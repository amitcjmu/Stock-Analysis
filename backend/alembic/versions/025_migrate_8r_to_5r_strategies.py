"""Migrate 8R to 6R strategy data

Revision ID: 025_migrate_8r_to_5r_strategies
Revises: 2ae8940123e6
Create Date: 2025-08-02 10:30:00.000000

"""

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "025_migrate_8r_to_5r_strategies"
down_revision = "2ae8940123e6"
branch_labels = None
depends_on = None

# Strategy mapping from old 8R system to new 6R system
STRATEGY_MIGRATION_MAP = {
    # Direct mappings (6R strategies)
    "rehost": "rehost",
    "replatform": "replatform",
    "refactor": "refactor",
    "rearchitect": "rearchitect",
    "replace": "replace",
    "rewrite": "rewrite",
    # Deprecated 8R strategies -> 6R equivalents
    "repurchase": "replace",  # Map to REPLACE
    "retire": "replace",  # Map to REPLACE (applications to be retired)
    "retain": "rehost",  # Map to REHOST (keep as-is for now)
}


def upgrade() -> None:
    """Migrate existing 8R strategy data to 6R framework."""

    connection = op.get_bind()

    print("Starting 6R strategy migration...")

    # Update assessment_flow_states table
    try:
        result = connection.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'assessment_flow_states' AND table_schema = 'public'
        """
            )
        )

        if result.scalar() > 0:
            for old_strategy, new_strategy in STRATEGY_MIGRATION_MAP.items():
                connection.execute(
                    text(
                        """
                    UPDATE assessment_flow_states
                    SET recommended_strategy = :new_strategy
                    WHERE recommended_strategy = :old_strategy
                """
                    ),
                    {"new_strategy": new_strategy, "old_strategy": old_strategy},
                )
            print("✓ Updated assessment_flow_states")
    except Exception as e:
        print(f"⚠ Warning: Could not update assessment_flow_states: {e}")

    # Update assessment_results table
    try:
        result = connection.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'assessment_results' AND table_schema = 'public'
        """
            )
        )

        if result.scalar() > 0:
            for old_strategy, new_strategy in STRATEGY_MIGRATION_MAP.items():
                connection.execute(
                    text(
                        """
                    UPDATE assessment_results
                    SET recommended_strategy = :new_strategy
                    WHERE recommended_strategy = :old_strategy
                """
                    ),
                    {"new_strategy": new_strategy, "old_strategy": old_strategy},
                )
            print("✓ Updated assessment_results")
    except Exception as e:
        print(f"⚠ Warning: Could not update assessment_results: {e}")

    # Update sixr_analysis_results enum (if exists)
    try:
        result = connection.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'sixr_analysis_results' AND table_schema = 'public'
        """
            )
        )

        if result.scalar() > 0:
            # Rename old enum
            connection.execute(
                text("ALTER TYPE sixrstrategy RENAME TO sixrstrategy_old;")
            )

            # Create new 6R enum
            connection.execute(
                text(
                    """
                CREATE TYPE sixrstrategy AS ENUM (
                    'rehost', 'replatform', 'refactor', 'rearchitect', 'replace', 'rewrite'
                );
            """
                )
            )

            # Update column to use new enum
            connection.execute(
                text(
                    """
                ALTER TABLE sixr_analysis_results
                ALTER COLUMN recommended_strategy TYPE sixrstrategy
                USING recommended_strategy::text::sixrstrategy;
            """
                )
            )

            # Drop old enum
            connection.execute(text("DROP TYPE sixrstrategy_old;"))
            print("✓ Updated sixr_analysis_results enum")
    except Exception as e:
        print(f"⚠ Warning: Could not update sixr_analysis_results enum: {e}")

    print("6R strategy migration completed successfully")


def downgrade() -> None:
    """Downgrade from 6R back to 8R framework (if needed)."""

    connection = op.get_bind()

    # Reverse strategy mappings (best effort - lossy operation)
    REVERSE_STRATEGY_MAP = {
        "rehost": "rehost",
        "replatform": "replatform",
        "refactor": "refactor",
        "rearchitect": "rearchitect",
        "replace": "repurchase",  # Default to repurchase
        "rewrite": "rewrite",
    }

    # Validate table names against strict whitelist
    ALLOWED_TABLES = {"assessment_flow_states", "assessment_results"}

    try:
        # Restore 8R enum
        connection.execute(text("ALTER TYPE sixrstrategy RENAME TO sixrstrategy_6r;"))

        connection.execute(
            text(
                """
            CREATE TYPE sixrstrategy AS ENUM (
                'rehost', 'replatform', 'refactor', 'rearchitect',
                'repurchase', 'retire', 'retain', 'rewrite'
            );
        """
            )
        )

        # Update tables back to 8R strategies
        table_names = ["assessment_flow_states", "assessment_results"]
        for table_name in table_names:
            # Validate table name against strict whitelist
            if table_name not in ALLOWED_TABLES:
                raise ValueError(f"Invalid table name: {table_name}")

            # Check if table exists before updating
            result = connection.execute(
                text(
                    """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = :table_name AND table_schema = 'public'
            """
                ),
                {"table_name": table_name},
            )

            if result.scalar() > 0:
                for new_strategy, old_strategy in REVERSE_STRATEGY_MAP.items():
                    # Use safe table name mapping to avoid SQL injection
                    if table_name == "assessment_flow_states":
                        update_query = text("""
                            UPDATE assessment_flow_states 
                            SET recommended_strategy = :old_strategy 
                            WHERE recommended_strategy = :new_strategy
                        """)
                    elif table_name == "assessment_results":
                        update_query = text("""
                            UPDATE assessment_results 
                            SET recommended_strategy = :old_strategy 
                            WHERE recommended_strategy = :new_strategy
                        """)
                    else:
                        continue  # Skip unknown tables
                    
                    connection.execute(
                        update_query,
                        {"old_strategy": old_strategy, "new_strategy": new_strategy},
                    )
                print(f"✓ Updated {table_name}")
            else:
                print(f"⚠ Warning: Table {table_name} does not exist, skipping")

        # Update sixr_analysis_results with enum conversion (if exists)
        result = connection.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'sixr_analysis_results' AND table_schema = 'public'
        """
            )
        )

        if result.scalar() > 0:
            connection.execute(
                text(
                    """
                ALTER TABLE sixr_analysis_results
                ALTER COLUMN recommended_strategy TYPE sixrstrategy
                USING recommended_strategy::text::sixrstrategy;
            """
                )
            )

            connection.execute(text("DROP TYPE sixrstrategy_6r;"))

        print("Downgrade to 8R strategy framework completed")

    except Exception as e:
        print(f"Error: Downgrade failed: {e}")
        # Re-raise the exception to ensure migration fails properly
        raise
