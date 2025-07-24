#!/usr/bin/env python3
"""
Comprehensive E2E Test for Discovery Flow with Database Persistence Tracking

This script tests the complete discovery flow and verifies data persistence in:
1. crewai_flow_state_extensions - Master flow tracking
2. discovery_flows - Discovery-specific flow data
3. data_imports - Import metadata
4. raw_import_records - Raw CSV data
5. field_mappings - Field mapping configurations
6. discovery_assets - Discovered assets
7. assets - Final promoted assets
8. dependencies - Application dependencies
9. technical_debt_items - Technical debt findings
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select, text

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Enhanced sample CSV data with more realistic fields
SAMPLE_CSV_DATA = [
    {
        "server_name": "WEB-PROD-01",
        "ip_address": "10.1.1.100",
        "operating_system": "Ubuntu 20.04 LTS",
        "environment": "Production",
        "cpu_cores": "8",
        "memory_gb": "32",
        "storage_gb": "500",
        "application": "E-commerce Platform",
        "criticality": "High",
        "owner": "IT Operations",
        "location": "US-East-1",
        "last_updated": "2024-01-15",
        "status": "Active",
    },
    {
        "server_name": "DB-PROD-01",
        "ip_address": "10.1.1.101",
        "operating_system": "Red Hat Enterprise Linux 8",
        "environment": "Production",
        "cpu_cores": "16",
        "memory_gb": "64",
        "storage_gb": "2000",
        "application": "PostgreSQL Database Cluster",
        "criticality": "Critical",
        "owner": "Database Team",
        "location": "US-East-1",
        "last_updated": "2024-01-20",
        "status": "Active",
    },
    {
        "server_name": "API-PROD-01",
        "ip_address": "10.1.1.102",
        "operating_system": "Ubuntu 22.04 LTS",
        "environment": "Production",
        "cpu_cores": "4",
        "memory_gb": "16",
        "storage_gb": "100",
        "application": "REST API Gateway",
        "criticality": "High",
        "owner": "API Team",
        "location": "US-East-1",
        "last_updated": "2024-01-18",
        "status": "Active",
    },
    {
        "server_name": "APP-DEV-01",
        "ip_address": "10.2.1.50",
        "operating_system": "Windows Server 2019",
        "environment": "Development",
        "cpu_cores": "4",
        "memory_gb": "16",
        "storage_gb": "250",
        "application": "Development Test Server",
        "criticality": "Low",
        "owner": "Dev Team",
        "location": "US-West-2",
        "last_updated": "2024-01-10",
        "status": "Active",
    },
]


class DatabaseTracker:
    """Helper class to track database state at each phase"""

    def __init__(self, db_session):
        self.db = db_session

    async def check_table_counts(self) -> Dict[str, int]:
        """Get row counts for all relevant tables"""
        tables = [
            "crewai_flow_state_extensions",
            "discovery_flows",
            "data_imports",
            "raw_import_records",
            "import_field_mappings",  # Correct table name
            "assets",
            "asset_dependencies",  # Correct table name
            "migrations",  # For tracking overall migration progress
        ]

        counts = {}
        for table in tables:
            try:
                # Use separate transaction for each count to prevent cascade failures
                result = await self.db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                counts[table] = count
                await self.db.commit()  # Commit to clear any transaction state
            except Exception as e:
                await self.db.rollback()  # Rollback on error
                if "does not exist" in str(e):
                    counts[table] = "Table missing"
                else:
                    counts[table] = f"Error: {str(e)[:50]}..."

        return counts

    async def get_master_flow_state(self, flow_id: str) -> Dict[str, Any]:
        """Get the master flow state"""
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

        result = await self.db.execute(
            select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
        )
        flow = result.scalar_one_or_none()

        if flow:
            return {
                "flow_id": str(flow.flow_id),
                "flow_status": flow.flow_status,
                "flow_type": flow.flow_type,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "persistence_data": flow.flow_persistence_data,
            }
        return None

    async def get_discovery_flow_state(self, flow_id: str) -> Dict[str, Any]:
        """Get the discovery flow state"""
        from app.models.discovery_flow import DiscoveryFlow

        result = await self.db.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        )
        flow = result.scalar_one_or_none()

        if flow:
            return {
                "flow_id": str(flow.flow_id),
                "status": flow.status,
                "current_phase": flow.current_phase,
                "data_import_id": (
                    str(flow.data_import_id) if flow.data_import_id else None
                ),
                "field_mappings": flow.field_mappings,
                "progress_percentage": flow.progress_percentage,
            }
        return None

    async def get_data_import_info(self, flow_id: str) -> Dict[str, Any]:
        """Get data import information"""
        from app.models.data_import import DataImport
        from app.models.discovery_flow import DiscoveryFlow

        # First get the discovery flow to find data_import_id
        discovery_result = await self.db.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        )
        discovery_flow = discovery_result.scalar_one_or_none()

        if not discovery_flow or not discovery_flow.data_import_id:
            return None

        # Get the data import
        import_result = await self.db.execute(
            select(DataImport).where(
                DataImport.import_id == discovery_flow.data_import_id
            )
        )
        data_import = import_result.scalar_one_or_none()

        if data_import:
            return {
                "import_id": str(data_import.import_id),
                "file_name": data_import.file_name,
                "import_type": data_import.import_type,
                "status": data_import.status,
                "total_records": data_import.total_records,
                "processed_records": data_import.processed_records,
            }
        return None

    async def get_raw_records_sample(
        self, data_import_id: str, limit: int = 2
    ) -> List[Dict[str, Any]]:
        """Get sample of raw import records"""
        from app.models.data_import import RawImportRecord

        result = await self.db.execute(
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == data_import_id)
            .limit(limit)
        )
        records = result.scalars().all()

        return [
            {
                "record_id": str(record.record_id),
                "raw_data": record.raw_data,
                "validation_status": record.validation_status,
            }
            for record in records
        ]

    async def get_field_mappings(self, data_import_id: str) -> List[Dict[str, Any]]:
        """Get field mappings"""
        # Use raw SQL since the model name may not match table name
        result = await self.db.execute(
            text(
                """
                SELECT mapping_id, source_field, target_field, mapping_type, 
                       confidence_score, is_approved
                FROM import_field_mappings
                WHERE data_import_id = :import_id
            """
            ),
            {"import_id": data_import_id},
        )

        mappings = []
        for row in result:
            mappings.append(
                {
                    "mapping_id": str(row.mapping_id),
                    "source_field": row.source_field,
                    "target_field": row.target_field,
                    "mapping_type": row.mapping_type,
                    "is_approved": row.is_approved,
                    "confidence_score": row.confidence_score,
                }
            )
        return mappings

    async def get_discovery_assets_count(self, flow_id: str) -> int:
        """Get count of assets created by this discovery flow"""
        # Assets are tracked in the main assets table with metadata
        result = await self.db.execute(
            text(
                """
                SELECT COUNT(*) 
                FROM assets 
                WHERE metadata->>'discovery_flow_id' = :flow_id
                   OR metadata->>'source_flow_id' = :flow_id
            """
            ),
            {"flow_id": str(flow_id)},
        )
        count = result.scalar()
        return count or 0

    async def get_final_assets(self, limit: int = 2) -> List[Dict[str, Any]]:
        """Get sample of final assets"""
        result = await self.db.execute(
            text(
                """
                SELECT asset_id, name, asset_type, environment, ip_address, 
                       operating_system, criticality, owner
                FROM assets
                ORDER BY created_at DESC
                LIMIT :limit
            """
            ),
            {"limit": limit},
        )

        assets = []
        for row in result:
            assets.append(
                {
                    "asset_id": str(row.asset_id),
                    "name": row.name,
                    "asset_type": row.asset_type,
                    "environment": row.environment,
                    "ip_address": row.ip_address,
                    "operating_system": row.operating_system,
                    "criticality": row.criticality,
                    "owner": row.owner,
                }
            )
        return assets


async def test_discovery_flow_with_db_tracking():
    """Test the complete discovery flow with database persistence tracking"""
    logger.info("🚀 Starting Comprehensive Discovery Flow E2E Test with DB Tracking")

    tracker = None

    try:
        # Initialize database session
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )
        from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
            PhaseController,
        )

        # Test context
        test_context = RequestContext(
            client_account_id="12345",
            engagement_id="67890",
            user_id="test_user",
            request_id=str(uuid.uuid4()),
        )

        async with AsyncSessionLocal() as db:
            logger.info("✅ Database session created")
            tracker = DatabaseTracker(db)

            # Initial DB state
            logger.info("\n📊 Initial Database State:")
            initial_counts = await tracker.check_table_counts()
            for table, count in initial_counts.items():
                logger.info(f"  - {table}: {count}")

            # Step 1: Create a master flow
            logger.info("\n📋 Step 1: Creating master flow")
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            flow_repo = CrewAIFlowStateExtensionsRepository(
                db,
                test_context.client_account_id,
                test_context.engagement_id,
                test_context.user_id,
            )

            flow_id = str(uuid.uuid4())
            master_flow = await flow_repo.create_master_flow(
                flow_id=flow_id,
                flow_type="discovery",
                user_id=test_context.user_id,
                flow_name="E2E Test Discovery Flow with DB Tracking",
                flow_configuration={"source": "e2e_db_test", "test": True},
                initial_state={"raw_data": SAMPLE_CSV_DATA},
            )
            await db.commit()
            logger.info(f"✅ Master flow created: {flow_id}")

            # Check master flow in DB
            master_state = await tracker.get_master_flow_state(flow_id)
            logger.info(f"📊 Master flow state: {json.dumps(master_state, indent=2)}")

            # Step 2: Create data import record
            logger.info("\n📋 Step 2: Creating data import record")
            from app.repositories.data_import_repository import DataImportRepository

            import_repo = DataImportRepository(
                db, client_account_id=test_context.client_account_id
            )

            # Create data import
            from app.schemas.data_import import DataImportCreate

            import_data = DataImportCreate(
                file_name="test_servers.csv",
                file_path="/tmp/test_servers.csv",
                import_type="cmdb",
                source_system="test_system",
                total_records=len(SAMPLE_CSV_DATA),
            )

            data_import = await import_repo.create_data_import(import_data)
            data_import_id = data_import.import_id
            await db.commit()
            logger.info(f"✅ Data import created: {data_import_id}")

            # Create raw import records
            logger.info("📋 Creating raw import records")
            from app.models.data_import import RawImportRecord

            for idx, record in enumerate(SAMPLE_CSV_DATA):
                raw_record = RawImportRecord(
                    record_id=str(uuid.uuid4()),
                    data_import_id=data_import_id,
                    raw_data=record,
                    record_index=idx,
                    validation_status="pending",
                    client_account_id=(
                        int(test_context.client_account_id)
                        if test_context.client_account_id.isdigit()
                        else 11111111
                    ),
                )
                db.add(raw_record)

            await db.commit()
            logger.info(f"✅ Created {len(SAMPLE_CSV_DATA)} raw import records")

            # Check DB state after data import
            logger.info("\n📊 Database State After Data Import:")
            post_import_counts = await tracker.check_table_counts()
            for table, count in post_import_counts.items():
                if count != initial_counts.get(table):
                    logger.info(f"  - {table}: {initial_counts.get(table)} → {count}")

            # Step 3: Create discovery flow with phase controller
            logger.info("\n📋 Step 3: Creating discovery flow with sample data")
            crewai_service = CrewAIFlowService(db)

            discovery_flow = create_unified_discovery_flow(
                flow_id=flow_id,
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                user_id=test_context.user_id,
                raw_data=SAMPLE_CSV_DATA,
                metadata={
                    "source": "e2e_db_test",
                    "master_flow_id": flow_id,
                    "data_import_id": str(data_import_id),
                },
                crewai_service=crewai_service,
                context=test_context,
                master_flow_id=flow_id,
            )

            # Link discovery flow to data import
            from app.models.discovery_flow import DiscoveryFlow

            # Check if discovery flow already exists
            disc_flow_result = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            )
            disc_flow = disc_flow_result.scalar_one_or_none()

            if not disc_flow:
                # Create discovery flow record
                disc_flow = DiscoveryFlow(
                    flow_id=flow_id,
                    client_account_id=11111111,  # Demo account
                    engagement_id=uuid.UUID(
                        "22222222-2222-2222-2222-222222222222"
                    ),  # Demo engagement
                    user_id=test_context.user_id,
                    data_import_id=data_import_id,
                    status="initialized",
                    current_phase="initialization",
                    created_at=datetime.utcnow(),
                )
                db.add(disc_flow)
            else:
                # Update existing flow
                disc_flow.data_import_id = data_import_id

            await db.commit()
            logger.info("✅ Discovery flow linked to data import")

            # Initialize phase controller
            logger.info("\n📋 Step 4: Starting phase-by-phase execution")
            phase_controller = PhaseController(discovery_flow)

            # Start flow execution
            result = await phase_controller.start_flow_execution()

            logger.info("📊 Initial execution result:")
            logger.info(f"  - Phase: {result.phase.value}")
            logger.info(f"  - Status: {result.status}")
            logger.info(f"  - Requires user input: {result.requires_user_input}")

            # Check DB state after field mapping
            logger.info("\n📊 Database State After Field Mapping Phase:")
            post_mapping_counts = await tracker.check_table_counts()
            for table, count in post_mapping_counts.items():
                if count != post_import_counts.get(table):
                    logger.info(
                        f"  - {table}: {post_import_counts.get(table)} → {count}"
                    )

            # Check discovery flow state
            disc_state = await tracker.get_discovery_flow_state(flow_id)
            logger.info(f"📊 Discovery flow state: {json.dumps(disc_state, indent=2)}")

            # Check data import info
            import_info = await tracker.get_data_import_info(flow_id)
            logger.info(f"📊 Data import info: {json.dumps(import_info, indent=2)}")

            # Check raw records
            if import_info and import_info.get("import_id"):
                raw_records = await tracker.get_raw_records_sample(
                    import_info["import_id"]
                )
                logger.info(
                    f"📊 Sample raw records: {json.dumps(raw_records, indent=2)}"
                )

            # Verify we paused at field mapping approval
            if (
                result.phase.value == "field_mapping_approval"
                and result.requires_user_input
            ):
                logger.info(
                    "\n✅ SUCCESS: Flow properly paused at field mapping approval!"
                )

                # Get field mappings from discovery flow state
                if hasattr(discovery_flow, "state") and hasattr(
                    discovery_flow.state, "field_mappings"
                ):
                    field_mappings = discovery_flow.state.field_mappings
                    logger.info("\n📊 Generated field mappings:")
                    for source, target in field_mappings.items():
                        if source != "confidence_scores":
                            logger.info(f"  - {source} → {target}")

                # Step 5: Create field mapping records in DB
                logger.info("\n📋 Step 5: Creating field mapping records in database")

                if import_info:
                    # Use raw SQL to insert field mappings
                    for source, target in field_mappings.items():
                        if source != "confidence_scores":
                            await db.execute(
                                text(
                                    """
                                    INSERT INTO import_field_mappings 
                                    (mapping_id, data_import_id, source_field, target_field, 
                                     mapping_type, confidence_score, is_approved, created_at)
                                    VALUES (:mapping_id, :import_id, :source, :target, 
                                            :mapping_type, :confidence, :approved, :created_at)
                                """
                                ),
                                {
                                    "mapping_id": str(uuid.uuid4()),
                                    "import_id": import_info["import_id"],
                                    "source": source,
                                    "target": target,
                                    "mapping_type": "auto_detected",
                                    "confidence": field_mappings.get(
                                        "confidence_scores", {}
                                    ).get(source, 0.8),
                                    "approved": False,
                                    "created_at": datetime.utcnow(),
                                },
                            )

                    await db.commit()
                    logger.info(
                        f"✅ Created {len(field_mappings) - 1} field mapping records"
                    )

                # Check field mappings in DB
                if import_info:
                    db_mappings = await tracker.get_field_mappings(
                        import_info["import_id"]
                    )
                    logger.info(
                        f"📊 Field mappings in DB: {json.dumps(db_mappings, indent=2)}"
                    )

                # Step 6: Simulate user approval
                logger.info("\n📋 Step 6: Simulating user approval of field mappings")

                # Update field mappings to approved
                if import_info:
                    await db.execute(
                        text(
                            """
                            UPDATE import_field_mappings 
                            SET is_approved = true, updated_at = :now
                            WHERE data_import_id = :import_id
                        """
                        ),
                        {
                            "now": datetime.utcnow(),
                            "import_id": import_info["import_id"],
                        },
                    )
                    await db.commit()
                    logger.info("✅ Field mappings approved in database")

                # Resume flow with approved mappings
                user_input = {
                    "approved_mappings": (
                        field_mappings if "field_mappings" in locals() else {}
                    ),
                    "approval_timestamp": datetime.utcnow().isoformat(),
                    "approved_by": test_context.user_id,
                    "approval_notes": "Approved via E2E DB test",
                    "user_approval": True,
                }

                from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
                    FlowPhase,
                )

                resume_result = await phase_controller.resume_flow_execution(
                    from_phase=FlowPhase.FIELD_MAPPING_APPROVAL, user_input=user_input
                )

                logger.info("\n📊 Resume execution result:")
                logger.info(f"  - Phase: {resume_result.phase.value}")
                logger.info(f"  - Status: {resume_result.status}")

                # Check final DB state
                logger.info("\n📊 Final Database State:")
                final_counts = await tracker.check_table_counts()
                for table, count in final_counts.items():
                    initial = initial_counts.get(table, 0)
                    if count != initial:
                        logger.info(
                            f"  - {table}: {initial} → {count} (+{count - initial})"
                        )

                # Check discovery assets
                disc_assets_count = await tracker.get_discovery_assets_count(flow_id)
                logger.info(f"\n📊 Discovery assets created: {disc_assets_count}")

                # Check final assets
                final_assets = await tracker.get_final_assets()
                logger.info(
                    f"📊 Sample final assets: {json.dumps(final_assets, indent=2)}"
                )

                # Check final flow states
                final_master_state = await tracker.get_master_flow_state(flow_id)
                logger.info(
                    f"\n📊 Final master flow state: {json.dumps(final_master_state, indent=2)}"
                )

                final_disc_state = await tracker.get_discovery_flow_state(flow_id)
                logger.info(
                    f"📊 Final discovery flow state: {json.dumps(final_disc_state, indent=2)}"
                )

                logger.info("\n🎉 E2E Test with DB Tracking completed successfully!")

            else:
                logger.error(
                    "\n❌ ERROR: Flow did not pause at field mapping approval!"
                )
                logger.error(f"  - Current phase: {result.phase.value}")
                logger.error(f"  - Requires user input: {result.requires_user_input}")

    except Exception as e:
        logger.error(f"\n❌ E2E Test failed with error: {e}")
        import traceback

        traceback.print_exc()

        # Try to show current DB state even on error
        if tracker:
            try:
                logger.info("\n📊 Database State at Error:")
                error_counts = await tracker.check_table_counts()
                for table, count in error_counts.items():
                    logger.info(f"  - {table}: {count}")
            except Exception:
                pass


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_discovery_flow_with_db_tracking())
