"""Create watchlist table

Revision ID: 157_create_watchlist_table
Revises: 156_create_stock_tables
Create Date: 2025-01-15

This migration creates the watchlist table for tracking user's favorite stocks.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "157_create_watchlist_table"
down_revision = "156_create_stock_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create watchlist table"""

    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema='migration'
                AND table_name='watchlists'
            ) THEN
                CREATE TABLE migration.watchlists (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    stock_symbol VARCHAR(20) NOT NULL,
                    stock_id UUID,
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,
                    user_id VARCHAR NOT NULL,
                    notes VARCHAR(500),
                    alert_price VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    CONSTRAINT fk_watchlists_stock_id
                        FOREIGN KEY (stock_id)
                        REFERENCES migration.stocks(id)
                        ON DELETE CASCADE,
                    CONSTRAINT uq_watchlist_user_stock
                        UNIQUE (client_account_id, engagement_id, user_id, stock_symbol)
                );

                CREATE INDEX IF NOT EXISTS ix_watchlists_stock_symbol ON migration.watchlists(stock_symbol);
                CREATE INDEX IF NOT EXISTS ix_watchlists_stock_id ON migration.watchlists(stock_id);
                CREATE INDEX IF NOT EXISTS ix_watchlists_client_account_id ON migration.watchlists(client_account_id);
                CREATE INDEX IF NOT EXISTS ix_watchlists_engagement_id ON migration.watchlists(engagement_id);
                CREATE INDEX IF NOT EXISTS ix_watchlists_user_id ON migration.watchlists(user_id);
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """Drop watchlist table"""
    op.execute(
        """
        DROP TABLE IF EXISTS migration.watchlists CASCADE;
    """
    )
