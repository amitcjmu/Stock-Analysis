"""add_analysis_queue_tables

Add analysis queue tables for batch processing applications.
Uses CHECK constraints instead of ENUMs for better flexibility per 000-lessons.md.

Revision ID: 064_add_analysis_queue_tables
Revises: 063_fix_enum_case_for_pattern_type
Create Date: 2025-09-11 16:00:00.000000

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "064_add_analysis_queue_tables"
down_revision = "063_fix_enum_case_for_pattern_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analysis queue tables in migration schema - idempotent"""

    print("🔧 Creating analysis queue tables...")

    # Set schema search path to migration schema
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    # Check if analysis_queues table already exists
    table_check = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'analysis_queues'
        """
        )
    )

    if table_check.fetchone():
        print("   ✅ analysis_queues table already exists - skipping creation")
        return

    print("   📝 Creating analysis_queues table...")

    # Create analysis_queues table with CHECK constraints (not ENUMs)
    op.execute(
        """
        CREATE TABLE migration.analysis_queues (
            id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            client_id UUID NOT NULL,
            engagement_id UUID NOT NULL,
            created_by UUID NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT analysis_queues_pkey PRIMARY KEY (id),
            CONSTRAINT analysis_queues_status_check CHECK (
                status IN ('pending', 'processing', 'paused', 'completed', 'cancelled', 'failed')
            )
        )
    """
    )

    print("   📝 Creating analysis_queue_items table...")

    # Create analysis_queue_items table
    op.execute(
        """
        CREATE TABLE migration.analysis_queue_items (
            id UUID NOT NULL,
            queue_id UUID NOT NULL,
            application_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE,
            error_message TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT analysis_queue_items_pkey PRIMARY KEY (id),
            CONSTRAINT analysis_queue_items_queue_id_fkey FOREIGN KEY (queue_id)
                REFERENCES migration.analysis_queues (id) ON DELETE CASCADE,
            CONSTRAINT analysis_queue_items_status_check CHECK (
                status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
            )
        )
    """
    )

    print("   📝 Creating indexes for performance...")

    # Create indexes for multi-tenant performance
    op.execute(
        """
        CREATE INDEX idx_analysis_queues_context
        ON migration.analysis_queues (client_id, engagement_id)
    """
    )

    op.execute(
        """
        CREATE INDEX idx_analysis_queue_items_queue_id
        ON migration.analysis_queue_items (queue_id)
    """
    )

    op.execute(
        """
        CREATE INDEX idx_analysis_queue_items_status
        ON migration.analysis_queue_items (status)
    """
    )

    print(
        "   ✅ Successfully created analysis queue tables with proper multi-tenant support"
    )


def downgrade() -> None:
    """Drop analysis queue tables - idempotent"""

    print("🔄 Dropping analysis queue tables...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    # Check if tables exist before dropping
    items_table_check = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'analysis_queue_items'
        """
        )
    )

    queues_table_check = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'analysis_queues'
        """
        )
    )

    # Drop indexes first if they exist
    if items_table_check.fetchone():
        print("   📝 Dropping analysis_queue_items table...")
        op.execute("DROP INDEX IF EXISTS migration.idx_analysis_queue_items_status")
        op.execute("DROP INDEX IF EXISTS migration.idx_analysis_queue_items_queue_id")
        op.execute("DROP TABLE migration.analysis_queue_items CASCADE")

    if queues_table_check.fetchone():
        print("   📝 Dropping analysis_queues table...")
        op.execute("DROP INDEX IF EXISTS migration.idx_analysis_queues_context")
        op.execute("DROP TABLE migration.analysis_queues CASCADE")

    print("   ✅ Analysis queue tables dropped successfully")
