"""Create stock analysis tables

Revision ID: 156_create_stock_tables
Revises: 155_fix_asset_unique_constraint_add_asset_type
Create Date: 2025-01-15

This migration creates tables for stock analysis application:
- stocks: Stores stock information and search results
- stock_analyses: Stores LLM-generated stock analysis
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "156_create_stock_tables"
down_revision = "155_fix_asset_unique_constraint_add_asset_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create stock and stock_analyses tables"""
    
    # Create stocks table
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema='migration'
                AND table_name='stocks'
            ) THEN
                CREATE TABLE migration.stocks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    symbol VARCHAR(20) NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    exchange VARCHAR(50),
                    sector VARCHAR(100),
                    industry VARCHAR(200),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,
                    user_id VARCHAR NOT NULL,
                    current_price DOUBLE PRECISION,
                    previous_close DOUBLE PRECISION,
                    market_cap DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    price_change DOUBLE PRECISION,
                    price_change_percent DOUBLE PRECISION,
                    stock_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
                    search_keywords TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS ix_stocks_symbol ON migration.stocks(symbol);
                CREATE INDEX IF NOT EXISTS ix_stocks_client_account_id ON migration.stocks(client_account_id);
                CREATE INDEX IF NOT EXISTS ix_stocks_engagement_id ON migration.stocks(engagement_id);
            END IF;
        END $$;
    """)
    
    # Create stock_analyses table
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema='migration'
                AND table_name='stock_analyses'
            ) THEN
                CREATE TABLE migration.stock_analyses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    stock_id UUID NOT NULL,
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,
                    user_id VARCHAR NOT NULL,
                    analysis_type VARCHAR(50) DEFAULT 'comprehensive' NOT NULL,
                    summary TEXT NOT NULL,
                    key_insights JSONB DEFAULT '[]'::jsonb NOT NULL,
                    technical_analysis JSONB,
                    fundamental_analysis JSONB,
                    risk_assessment JSONB,
                    recommendations JSONB,
                    price_targets JSONB,
                    llm_model VARCHAR(100),
                    llm_prompt TEXT,
                    llm_response JSONB,
                    confidence_score DOUBLE PRECISION,
                    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    is_latest VARCHAR(10) DEFAULT 'true' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    CONSTRAINT fk_stock_analyses_stock_id 
                        FOREIGN KEY (stock_id) 
                        REFERENCES migration.stocks(id) 
                        ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS ix_stock_analyses_stock_id ON migration.stock_analyses(stock_id);
                CREATE INDEX IF NOT EXISTS ix_stock_analyses_client_account_id ON migration.stock_analyses(client_account_id);
                CREATE INDEX IF NOT EXISTS ix_stock_analyses_engagement_id ON migration.stock_analyses(engagement_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Drop stock analysis tables"""
    op.execute("""
        DROP TABLE IF EXISTS migration.stock_analyses CASCADE;
    """)
    op.execute("""
        DROP TABLE IF EXISTS migration.stocks CASCADE;
    """)

