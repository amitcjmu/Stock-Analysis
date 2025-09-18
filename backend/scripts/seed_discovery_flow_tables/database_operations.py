"""
Database operations for seeding discovery flow tables.
"""

import logging
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def drop_existing_tables():
    """Drop existing discovery flow tables to start fresh"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🗑️  Dropping existing discovery flow tables...")

            # Drop tables in correct order (assets first due to foreign keys)
            await session.execute(text("DROP TABLE IF EXISTS discovery_assets CASCADE"))
            await session.execute(text("DROP TABLE IF EXISTS discovery_flows CASCADE"))

            await session.commit()
            logger.info("✅ Existing tables dropped successfully")

        except Exception as e:
            logger.warning(f"⚠️  Error dropping tables (may not exist): {e}")
            await session.rollback()


async def create_fresh_tables():
    """Create fresh discovery flow tables with proper structure"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🏗️  Creating fresh discovery flow tables...")

            # Create discovery_flows table
            create_flows_sql = """
            CREATE TABLE IF NOT EXISTS discovery_flows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flow_id UUID UNIQUE NOT NULL,
                client_account_id UUID NOT NULL,
                engagement_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                current_phase VARCHAR(50),
                progress_percentage DECIMAL(5,2) DEFAULT 0.0,
                status VARCHAR(50) DEFAULT 'pending',
                raw_data JSONB,
                field_mappings JSONB,
                asset_inventory JSONB,
                dependencies JSONB,
                tech_debt_assessment JSONB,
                migration_assessment JSONB,
                remediation_plan JSONB,
                completion_timestamp TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """

            await session.execute(text(create_flows_sql))

            # Create discovery_assets table
            create_assets_sql = """
            CREATE TABLE IF NOT EXISTS discovery_assets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                discovery_flow_id UUID NOT NULL REFERENCES discovery_flows(id) ON DELETE CASCADE,
                client_account_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                asset_type VARCHAR(100),
                asset_subtype VARCHAR(100),
                description TEXT,
                status VARCHAR(50) DEFAULT 'discovered',
                criticality VARCHAR(20) DEFAULT 'medium',
                discovered_in_phase VARCHAR(50),
                discovery_method VARCHAR(100),
                quality_score DECIMAL(3,2) DEFAULT 0.0,
                confidence_score DECIMAL(3,2) DEFAULT 0.0,
                validation_status VARCHAR(50) DEFAULT 'pending',
                tech_debt_score DECIMAL(3,2) DEFAULT 0.0,
                modernization_priority VARCHAR(20),
                six_r_recommendation VARCHAR(50),
                migration_ready BOOLEAN DEFAULT FALSE,
                migration_blockers TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """

            await session.execute(text(create_assets_sql))

            # Create indexes
            await session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_discovery_flows_flow_id ON discovery_flows(flow_id);"
                )
            )
            await session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_discovery_assets_flow_id ON discovery_assets(discovery_flow_id);"
                )
            )

            await session.commit()
            logger.info("✅ Fresh tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            await session.rollback()
            raise


async def verify_seeded_data():
    """Verify that data was seeded correctly"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🔍 Verifying seeded data...")

            # Count flows
            flows_result = await session.execute(
                text("SELECT COUNT(*) FROM discovery_flows")
            )
            flows_count = flows_result.scalar()

            # Count assets
            assets_result = await session.execute(
                text("SELECT COUNT(*) FROM discovery_assets")
            )
            assets_count = assets_result.scalar()

            logger.info("✅ Verification complete:")
            logger.info(f"   📋 Discovery Flows: {flows_count}")
            logger.info(f"   🏗️  Discovery Assets: {assets_count}")

            return flows_count > 0 and assets_count > 0

        except Exception as e:
            logger.error(f"❌ Error verifying data: {e}")
            return False
