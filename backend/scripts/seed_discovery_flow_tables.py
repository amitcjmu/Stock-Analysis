#!/usr/bin/env python3
"""
Discovery Flow Database Seeding Script
Phase 3: Database Integration & Seeding

This script:
1. Drops existing discovery flow tables (since it's test data)
2. Creates fresh tables with proper ecosystem integration
3. Seeds with demo data for testing
4. Eliminates session_id dependencies completely
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from app.core.database import AsyncSessionLocal
    from app.models.asset import Asset as DiscoveryAsset
    from app.models.client_account import ClientAccount, Engagement, User
    from app.models.data_import.core import DataImport
    from app.models.data_import_session import DataImportSession
    from app.models.discovery_flow import DiscoveryFlow
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    DEPENDENCIES_AVAILABLE = False
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo constants for multi-tenant testing
DEMO_CLIENT_ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "demo_user"
DEMO_IMPORT_SESSION_ID = "33333333-3333-3333-3333-333333333333"

# Sample discovery flow data
SAMPLE_DISCOVERY_FLOWS = [
    {
        "flow_id": uuid.UUID("f1111111-1111-1111-1111-111111111111"),
        "name": "Demo CMDB Discovery",
        "description": "Initial discovery of enterprise CMDB data",
        "current_phase": "completed",
        "progress_percentage": 100.0,
        "status": "completed",
        "raw_data": [
            {
                "hostname": "web-server-01",
                "ip_address": "10.0.1.10",
                "os": "Windows Server 2019",
                "cpu_cores": 4,
                "memory_gb": 16,
                "application": "IIS Web Server",
            },
            {
                "hostname": "db-server-01",
                "ip_address": "10.0.1.20",
                "os": "SQL Server 2019",
                "cpu_cores": 8,
                "memory_gb": 32,
                "application": "SQL Server Database",
            },
            {
                "hostname": "app-server-01",
                "ip_address": "10.0.1.30",
                "os": "Windows Server 2019",
                "cpu_cores": 4,
                "memory_gb": 8,
                "application": "Custom Business App",
            },
        ],
        "field_mappings": {
            "hostname": "asset_name",
            "ip_address": "ip_address",
            "os": "operating_system",
            "cpu_cores": "cpu_cores",
            "memory_gb": "memory_gb",
            "application": "primary_application",
        },
        "asset_inventory": {
            "total_assets": 3,
            "by_type": {"server": 3, "database": 1, "application": 2},
            "by_os": {"Windows Server 2019": 2, "SQL Server 2019": 1},
        },
        "dependencies": {
            "identified": [
                {
                    "source": "app-server-01",
                    "target": "db-server-01",
                    "type": "database_connection",
                },
                {
                    "source": "web-server-01",
                    "target": "app-server-01",
                    "type": "application_api",
                },
            ]
        },
        "tech_debt": {
            "high_risk_assets": ["db-server-01"],
            "modernization_candidates": ["web-server-01", "app-server-01"],
            "overall_score": 65.5,
        },
        "assessment_package": {
            "assets_ready": 3,
            "dependencies_mapped": 2,
            "migration_blockers": 0,
            "recommended_waves": 2,
        },
    },
    {
        "flow_id": uuid.UUID("f2222222-2222-2222-2222-222222222222"),
        "name": "Infrastructure Refresh Discovery",
        "description": "Discovery for infrastructure refresh project",
        "current_phase": "inventory",
        "progress_percentage": 66.7,
        "status": "active",
        "raw_data": [
            {
                "hostname": "legacy-server-01",
                "ip_address": "192.168.1.100",
                "os": "Windows Server 2012",
                "cpu_cores": 2,
                "memory_gb": 8,
                "application": "Legacy ERP System",
            }
        ],
        "field_mappings": {
            "hostname": "asset_name",
            "ip_address": "ip_address",
            "os": "operating_system",
            "cpu_cores": "cpu_cores",
            "memory_gb": "memory_gb",
        },
        "asset_inventory": {
            "total_assets": 1,
            "by_type": {"server": 1},
            "by_os": {"Windows Server 2012": 1},
        },
        "dependencies": {},
        "tech_debt": {},
        "assessment_package": {},
    },
]

# Sample discovery assets
SAMPLE_DISCOVERY_ASSETS = [
    # Assets for first flow
    {
        "flow_id": uuid.UUID("f1111111-1111-1111-1111-111111111111"),
        "asset_name": "web-server-01",
        "asset_type": "server",
        "asset_subtype": "web_server",
        "asset_data": {
            "hostname": "web-server-01",
            "ip_address": "10.0.1.10",
            "operating_system": "Windows Server 2019",
            "cpu_cores": 4,
            "memory_gb": 16,
            "primary_application": "IIS Web Server",
            "environment": "production",
            "location": "datacenter-east",
        },
        "discovered_in_phase": "inventory",
        "discovery_method": "cmdb_import",
        "quality_score": 0.95,
        "confidence_score": 0.90,
        "validation_status": "validated",
        "tech_debt_score": 0.7,
        "modernization_priority": "medium",
        "six_r_recommendation": "replatform",
        "migration_ready": True,
    },
    {
        "flow_id": uuid.UUID("f1111111-1111-1111-1111-111111111111"),
        "asset_name": "db-server-01",
        "asset_type": "database",
        "asset_subtype": "sql_server",
        "asset_data": {
            "hostname": "db-server-01",
            "ip_address": "10.0.1.20",
            "operating_system": "SQL Server 2019",
            "cpu_cores": 8,
            "memory_gb": 32,
            "primary_application": "SQL Server Database",
            "environment": "production",
            "location": "datacenter-east",
        },
        "discovered_in_phase": "inventory",
        "discovery_method": "cmdb_import",
        "quality_score": 0.98,
        "confidence_score": 0.95,
        "validation_status": "validated",
        "tech_debt_score": 0.3,
        "modernization_priority": "low",
        "six_r_recommendation": "rehost",
        "migration_ready": True,
    },
    {
        "flow_id": uuid.UUID("f1111111-1111-1111-1111-111111111111"),
        "asset_name": "app-server-01",
        "asset_type": "application",
        "asset_subtype": "business_application",
        "asset_data": {
            "hostname": "app-server-01",
            "ip_address": "10.0.1.30",
            "operating_system": "Windows Server 2019",
            "cpu_cores": 4,
            "memory_gb": 8,
            "primary_application": "Custom Business App",
            "environment": "production",
            "location": "datacenter-east",
        },
        "discovered_in_phase": "inventory",
        "discovery_method": "cmdb_import",
        "quality_score": 0.85,
        "confidence_score": 0.80,
        "validation_status": "validated",
        "tech_debt_score": 0.8,
        "modernization_priority": "high",
        "six_r_recommendation": "refactor",
        "migration_ready": False,
        "migration_blockers": ["legacy_dependencies", "custom_code_review_needed"],
    },
    # Assets for second flow
    {
        "flow_id": uuid.UUID("f2222222-2222-2222-2222-222222222222"),
        "asset_name": "legacy-server-01",
        "asset_type": "server",
        "asset_subtype": "application_server",
        "asset_data": {
            "hostname": "legacy-server-01",
            "ip_address": "192.168.1.100",
            "operating_system": "Windows Server 2012",
            "cpu_cores": 2,
            "memory_gb": 8,
            "primary_application": "Legacy ERP System",
            "environment": "production",
            "location": "datacenter-west",
        },
        "discovered_in_phase": "inventory",
        "discovery_method": "cmdb_import",
        "quality_score": 0.60,
        "confidence_score": 0.70,
        "validation_status": "pending",
        "tech_debt_score": 0.9,
        "modernization_priority": "critical",
        "six_r_recommendation": "retire",
        "migration_ready": False,
        "migration_blockers": ["end_of_life_os", "business_process_review_needed"],
    },
]


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
    """Create fresh discovery flow tables with proper integration"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🏗️  Creating fresh discovery flow tables...")

            # Create discovery_flows table
            create_flows_sql = """
            CREATE TABLE discovery_flows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flow_id UUID UNIQUE NOT NULL,
                client_account_id UUID NOT NULL,
                engagement_id UUID NOT NULL,
                user_id VARCHAR NOT NULL,
                import_session_id UUID,
                data_import_id UUID,
                flow_name VARCHAR(255) NOT NULL,
                flow_description TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                progress_percentage FLOAT NOT NULL DEFAULT 0.0,
                data_import_completed BOOLEAN NOT NULL DEFAULT FALSE,
                attribute_mapping_completed BOOLEAN NOT NULL DEFAULT FALSE,
                data_cleansing_completed BOOLEAN NOT NULL DEFAULT FALSE,
                inventory_completed BOOLEAN NOT NULL DEFAULT FALSE,
                dependencies_completed BOOLEAN NOT NULL DEFAULT FALSE,
                tech_debt_completed BOOLEAN NOT NULL DEFAULT FALSE,
                crewai_persistence_id UUID,
                crewai_state_data JSONB NOT NULL DEFAULT '{}',
                learning_scope VARCHAR(50) NOT NULL DEFAULT 'engagement',
                memory_isolation_level VARCHAR(20) NOT NULL DEFAULT 'strict',
                assessment_ready BOOLEAN NOT NULL DEFAULT FALSE,
                assessment_package JSONB,
                is_mock BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            );
            """

            # Create discovery_assets table
            create_assets_sql = """
            CREATE TABLE discovery_assets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                discovery_flow_id UUID NOT NULL,
                client_account_id UUID NOT NULL,
                engagement_id UUID NOT NULL,
                asset_name VARCHAR(255) NOT NULL,
                asset_type VARCHAR(100),
                asset_subtype VARCHAR(100),
                raw_data JSONB NOT NULL,
                normalized_data JSONB,
                discovered_in_phase VARCHAR(50) NOT NULL,
                discovery_method VARCHAR(100),
                confidence_score FLOAT,
                migration_ready BOOLEAN NOT NULL DEFAULT FALSE,
                migration_complexity VARCHAR(20),
                migration_priority INTEGER,
                asset_status VARCHAR(20) NOT NULL DEFAULT 'discovered',
                validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                is_mock BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                FOREIGN KEY (discovery_flow_id) REFERENCES discovery_flows(id) ON DELETE CASCADE
            );
            """

            # Create indexes (execute individually)
            index_commands = [
                "CREATE INDEX ix_discovery_flows_flow_id ON discovery_flows(flow_id)",
                "CREATE INDEX ix_discovery_flows_client_account_id ON discovery_flows(client_account_id)",
                "CREATE INDEX ix_discovery_flows_engagement_id ON discovery_flows(engagement_id)",
                "CREATE INDEX ix_discovery_flows_status ON discovery_flows(status)",
                "CREATE INDEX ix_discovery_flows_is_mock ON discovery_flows(is_mock)",
                "CREATE INDEX ix_discovery_assets_discovery_flow_id ON discovery_assets(discovery_flow_id)",
                "CREATE INDEX ix_discovery_assets_client_account_id ON discovery_assets(client_account_id)",
                "CREATE INDEX ix_discovery_assets_engagement_id ON discovery_assets(engagement_id)",
                "CREATE INDEX ix_discovery_assets_asset_type ON discovery_assets(asset_type)",
                "CREATE INDEX ix_discovery_assets_asset_status ON discovery_assets(asset_status)",
                "CREATE INDEX ix_discovery_assets_is_mock ON discovery_assets(is_mock)",
            ]

            await session.execute(text(create_flows_sql))
            await session.execute(text(create_assets_sql))

            # Execute each index command individually
            for index_cmd in index_commands:
                await session.execute(text(index_cmd))

            await session.commit()
            logger.info("✅ Fresh tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            await session.rollback()
            raise


async def seed_demo_data():
    """Seed with demo discovery flow data"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🌱 Seeding demo discovery flow data...")

            # Create demo discovery flow
            demo_flow_id = uuid.uuid4()
            demo_flow = {
                "id": uuid.uuid4(),
                "flow_id": demo_flow_id,
                "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                "engagement_id": DEMO_ENGAGEMENT_ID,
                "user_id": DEMO_USER_ID,
                "import_session_id": DEMO_IMPORT_SESSION_ID,
                "flow_name": "Demo Discovery Flow - Clean Architecture",
                "flow_description": "Demonstration flow showing CrewAI Flow ID as single source of truth",
                "status": "active",
                "progress_percentage": 50.0,
                "data_import_completed": True,
                "attribute_mapping_completed": True,
                "data_cleansing_completed": True,
                "inventory_completed": False,
                "dependencies_completed": False,
                "tech_debt_completed": False,
                "crewai_state_data": json.dumps(
                    {
                        "flow_type": "discovery",
                        "architecture": "clean_flow_id_based",
                        "session_id_eliminated": True,
                    }
                ),
                "learning_scope": "engagement",
                "memory_isolation_level": "strict",
                "is_mock": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            # Insert demo flow
            insert_flow_sql = """
            INSERT INTO discovery_flows (
                id, flow_id, client_account_id, engagement_id, user_id, import_session_id,
                flow_name, flow_description, status, progress_percentage,
                data_import_completed, attribute_mapping_completed, data_cleansing_completed,
                inventory_completed, dependencies_completed, tech_debt_completed,
                crewai_state_data, learning_scope, memory_isolation_level, is_mock,
                created_at, updated_at
            ) VALUES (
                :id, :flow_id, :client_account_id, :engagement_id, :user_id, :import_session_id,
                :flow_name, :flow_description, :status, :progress_percentage,
                :data_import_completed, :attribute_mapping_completed, :data_cleansing_completed,
                :inventory_completed, :dependencies_completed, :tech_debt_completed,
                :crewai_state_data, :learning_scope, :memory_isolation_level, :is_mock,
                :created_at, :updated_at
            )
            """

            await session.execute(text(insert_flow_sql), demo_flow)

            # Create demo assets
            demo_assets = [
                {
                    "id": uuid.uuid4(),
                    "discovery_flow_id": demo_flow["id"],
                    "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                    "engagement_id": DEMO_ENGAGEMENT_ID,
                    "asset_name": "Web Server - Apache",
                    "asset_type": "server",
                    "asset_subtype": "web_server",
                    "raw_data": json.dumps(
                        {
                            "hostname": "web01.demo.com",
                            "ip_address": "192.168.1.10",
                            "os": "Ubuntu 20.04",
                            "cpu_cores": 4,
                            "memory_gb": 16,
                            "disk_gb": 500,
                        }
                    ),
                    "discovered_in_phase": "data_import",
                    "discovery_method": "cmdb_import",
                    "confidence_score": 0.95,
                    "migration_ready": True,
                    "migration_complexity": "medium",
                    "migration_priority": 2,
                    "asset_status": "validated",
                    "validation_status": "approved",
                    "is_mock": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                {
                    "id": uuid.uuid4(),
                    "discovery_flow_id": demo_flow["id"],
                    "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                    "engagement_id": DEMO_ENGAGEMENT_ID,
                    "asset_name": "Database Server - PostgreSQL",
                    "asset_type": "database",
                    "asset_subtype": "postgresql",
                    "raw_data": json.dumps(
                        {
                            "hostname": "db01.demo.com",
                            "ip_address": "192.168.1.20",
                            "os": "CentOS 8",
                            "version": "PostgreSQL 13",
                            "cpu_cores": 8,
                            "memory_gb": 32,
                            "disk_gb": 1000,
                        }
                    ),
                    "discovered_in_phase": "data_import",
                    "discovery_method": "network_scan",
                    "confidence_score": 0.88,
                    "migration_ready": False,
                    "migration_complexity": "high",
                    "migration_priority": 1,
                    "asset_status": "needs_review",
                    "validation_status": "pending",
                    "is_mock": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                {
                    "id": uuid.uuid4(),
                    "discovery_flow_id": demo_flow["id"],
                    "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
                    "engagement_id": DEMO_ENGAGEMENT_ID,
                    "asset_name": "CRM Application",
                    "asset_type": "application",
                    "asset_subtype": "web_application",
                    "raw_data": json.dumps(
                        {
                            "name": "Customer Relationship Management",
                            "technology": "Java Spring Boot",
                            "version": "2.5.0",
                            "dependencies": ["PostgreSQL", "Redis", "Elasticsearch"],
                            "users": 150,
                            "criticality": "high",
                        }
                    ),
                    "discovered_in_phase": "attribute_mapping",
                    "discovery_method": "application_scan",
                    "confidence_score": 0.92,
                    "migration_ready": True,
                    "migration_complexity": "medium",
                    "migration_priority": 3,
                    "asset_status": "validated",
                    "validation_status": "approved",
                    "is_mock": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            ]

            # Insert demo assets
            insert_asset_sql = """
            INSERT INTO discovery_assets (
                id, discovery_flow_id, client_account_id, engagement_id,
                asset_name, asset_type, asset_subtype, raw_data,
                discovered_in_phase, discovery_method, confidence_score,
                migration_ready, migration_complexity, migration_priority,
                asset_status, validation_status, is_mock,
                created_at, updated_at
            ) VALUES (
                :id, :discovery_flow_id, :client_account_id, :engagement_id,
                :asset_name, :asset_type, :asset_subtype, :raw_data,
                :discovered_in_phase, :discovery_method, :confidence_score,
                :migration_ready, :migration_complexity, :migration_priority,
                :asset_status, :validation_status, :is_mock,
                :created_at, :updated_at
            )
            """

            for asset in demo_assets:
                await session.execute(text(insert_asset_sql), asset)

            await session.commit()
            logger.info(f"✅ Seeded 1 discovery flow with {len(demo_assets)} assets")

        except Exception as e:
            logger.error(f"❌ Error seeding data: {e}")
            await session.rollback()
            raise


async def verify_seeded_data():
    """Verify the seeded data is accessible"""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🔍 Verifying seeded data...")

            # Count flows
            flow_count = await session.execute(
                text("SELECT COUNT(*) FROM discovery_flows")
            )
            flow_total = flow_count.scalar()

            # Count assets
            asset_count = await session.execute(
                text("SELECT COUNT(*) FROM discovery_assets")
            )
            asset_total = asset_count.scalar()

            # Get flow details
            flow_details = await session.execute(
                text(
                    """
                SELECT flow_id, flow_name, status, progress_percentage,
                       data_import_completed, attribute_mapping_completed, data_cleansing_completed
                FROM discovery_flows
                WHERE is_mock = true
            """
                )
            )

            logger.info("📊 Database verification:")
            logger.info(f"   • Discovery flows: {flow_total}")
            logger.info(f"   • Discovery assets: {asset_total}")

            for flow in flow_details:
                logger.info(f"   • Flow: {flow.flow_name}")
                logger.info(f"     - ID: {flow.flow_id}")
                logger.info(f"     - Status: {flow.status}")
                logger.info(f"     - Progress: {flow.progress_percentage}%")
                logger.info(
                    f"     - Phases: Import={flow.data_import_completed}, Mapping={flow.attribute_mapping_completed}, Cleansing={flow.data_cleansing_completed}"
                )

            logger.info("✅ Data verification completed successfully")

        except Exception as e:
            logger.error(f"❌ Error verifying data: {e}")
            raise


async def main():
    """Main seeding function"""
    logger.info("🚀 Starting Discovery Flow Database Seeding...")
    logger.info("=" * 60)

    try:
        # Step 1: Drop existing tables
        await drop_existing_tables()

        # Step 2: Create fresh tables
        await create_fresh_tables()

        # Step 3: Seed demo data
        await seed_demo_data()

        # Step 4: Verify seeded data
        await verify_seeded_data()

        logger.info("=" * 60)
        logger.info("✅ Discovery Flow Database Seeding Completed Successfully!")
        logger.info("\n🎯 Key Achievements:")
        logger.info("   • Eliminated session_id dependencies completely")
        logger.info("   • CrewAI Flow ID as single source of truth")
        logger.info("   • Fresh tables with proper ecosystem integration")
        logger.info("   • Multi-tenant isolation with demo constants")
        logger.info("   • Seeded with realistic demo data")
        logger.info("\n🔗 Integration Points:")
        logger.info("   • client_accounts table (via client_account_id)")
        logger.info("   • engagements table (via engagement_id)")
        logger.info("   • users table (via user_id)")
        logger.info("   • data_import_sessions table (via import_session_id)")
        logger.info("\n🎪 Ready for V2 API testing and frontend integration!")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
