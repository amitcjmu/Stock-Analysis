"""Create feedback and feedback_summaries tables

Revision ID: 143_create_feedback_tables
Revises: 142_fix_critical_constraints_bugs_1167_1168
Create Date: 2025-12-03
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "143_create_feedback_tables"
down_revision = "142_fix_critical_constraints_bugs_1167_1168"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create feedback and feedback_summaries tables."""

    # ==========================================================================
    # Create feedback table
    # ==========================================================================
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration' AND table_name = 'feedback'
            ) THEN
                CREATE TABLE migration.feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    feedback_type VARCHAR(50) NOT NULL,
                    page VARCHAR(255),
                    rating INTEGER,
                    comment TEXT,
                    category VARCHAR(50) DEFAULT 'general',
                    breadcrumb VARCHAR(500),
                    filename VARCHAR(255),
                    original_analysis JSONB,
                    user_corrections JSONB,
                    asset_type_override VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'new',
                    processed BOOLEAN DEFAULT FALSE,
                    user_agent VARCHAR(500),
                    user_timestamp VARCHAR(50),
                    client_ip VARCHAR(45),
                    client_account_id UUID REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
                    engagement_id UUID REFERENCES migration.engagements(id) ON DELETE CASCADE,
                    learning_patterns_extracted JSONB,
                    confidence_impact FLOAT DEFAULT 0.0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ,
                    processed_at TIMESTAMPTZ
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_feedback_id ON migration.feedback(id);
                CREATE INDEX IF NOT EXISTS idx_feedback_type ON migration.feedback(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_page ON migration.feedback(page);
                CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON migration.feedback(created_at DESC);

                RAISE NOTICE 'Created feedback table';
            ELSE
                RAISE NOTICE 'feedback table already exists';
            END IF;
        END $$;
        """
    )

    # ==========================================================================
    # Create feedback_summaries table
    # ==========================================================================
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration' AND table_name = 'feedback_summaries'
            ) THEN
                CREATE TABLE migration.feedback_summaries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    feedback_type VARCHAR(50) NOT NULL,
                    page VARCHAR(255),
                    time_period VARCHAR(20) DEFAULT 'all_time',
                    total_feedback INTEGER DEFAULT 0,
                    average_rating FLOAT DEFAULT 0.0,
                    status_counts JSONB,
                    rating_distribution JSONB,
                    category_counts JSONB,
                    feedback_trend JSONB,
                    rating_trend JSONB,
                    client_account_id UUID REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
                    engagement_id UUID REFERENCES migration.engagements(id) ON DELETE CASCADE,
                    last_calculated TIMESTAMPTZ DEFAULT NOW(),
                    calculation_duration_ms INTEGER
                );

                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_feedback_summaries_id ON migration.feedback_summaries(id);
                CREATE INDEX IF NOT EXISTS idx_feedback_summaries_type ON migration.feedback_summaries(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_summaries_page ON migration.feedback_summaries(page);

                RAISE NOTICE 'Created feedback_summaries table';
            ELSE
                RAISE NOTICE 'feedback_summaries table already exists';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Drop feedback tables."""
    op.execute(
        """
        DROP TABLE IF EXISTS migration.feedback_summaries CASCADE;
        DROP TABLE IF EXISTS migration.feedback CASCADE;
        """
    )
