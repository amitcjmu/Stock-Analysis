#!/usr/bin/env python3
"""
Simplified E2E Test for Discovery Flow with Database Tracking

This version uses separate sessions for different operations to avoid transaction conflicts.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample CSV data
SAMPLE_CSV_DATA = [
    {
        "server_name": "WEB-PROD-01",
        "ip_address": "10.1.1.100", 
        "operating_system": "Ubuntu 20.04",
        "environment": "Production",
        "cpu_cores": "8",
        "memory_gb": "32",
        "storage_gb": "500",
        "application": "E-commerce Platform",
        "criticality": "High",
        "owner": "IT Operations"
    },
    {
        "server_name": "DB-PROD-01",
        "ip_address": "10.1.1.101",
        "operating_system": "Red Hat 8",
        "environment": "Production", 
        "cpu_cores": "16",
        "memory_gb": "64",
        "storage_gb": "2000",
        "application": "PostgreSQL Database",
        "criticality": "Critical",
        "owner": "Database Team"
    }
]


async def check_db_state(phase_name: str):
    """Check database state at a specific phase"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text
    
    logger.info(f"\n📊 Database State - {phase_name}:")
    
    async with AsyncSessionLocal() as db:
        # Check key tables
        tables = {
            'crewai_flow_state_extensions': 'Master flows',
            'discovery_flows': 'Discovery flows',
            'data_imports': 'Data imports',
            'raw_import_records': 'Raw records',
            'import_field_mappings': 'Field mappings',
            'assets': 'Assets'
        }
        
        for table, desc in tables.items():
            try:
                result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                logger.info(f"  - {desc} ({table}): {count}")
            except Exception as e:
                logger.info(f"  - {desc} ({table}): Error - {str(e)[:50]}")


async def test_discovery_flow_simple():
    """Run a simplified E2E test focusing on core functionality"""
    
    logger.info("🚀 Starting Simplified Discovery Flow E2E Test")
    
    try:
        from app.core.database import AsyncSessionLocal
        from app.core.context import RequestContext
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
        from app.services.crewai_flows.unified_discovery_flow.phase_controller import PhaseController, FlowPhase
        from sqlalchemy import text, select
        
        # Test context - use proper demo UUIDs
        test_context = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",  # Demo client
            engagement_id="22222222-2222-2222-2222-222222222222",  # Demo engagement
            user_id="test_user",
            request_id=str(uuid.uuid4())
        )
        
        flow_id = str(uuid.uuid4())
        data_import_id = None
        
        # Check initial state
        await check_db_state("Initial")
        
        # Step 1: Create master flow
        logger.info(f"\n📋 Step 1: Creating master flow {flow_id}")
        async with AsyncSessionLocal() as db:
            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
            
            flow_repo = CrewAIFlowStateExtensionsRepository(
                db,
                test_context.client_account_id,
                test_context.engagement_id,
                test_context.user_id
            )
            
            master_flow = await flow_repo.create_master_flow(
                flow_id=flow_id,
                flow_type="discovery",
                user_id=test_context.user_id,
                flow_name="Simple E2E Test Flow"
            )
            await db.commit()
            logger.info(f"✅ Master flow created")
        
        # Step 2: Create data import
        logger.info("\n📋 Step 2: Creating data import record")
        async with AsyncSessionLocal() as db:
            # Create data import
            data_import_uuid = str(uuid.uuid4())
            
            # Get demo user ID
            demo_user_result = await db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "chocka@gmail.com"}
            )
            demo_user = demo_user_result.scalar()
            if not demo_user:
                # Use hardcoded demo user ID
                demo_user = uuid.UUID("33333333-3333-3333-3333-333333333333")
            
            result = await db.execute(
                text("""
                    INSERT INTO data_imports 
                    (id, client_account_id, engagement_id, import_name, filename, 
                     import_type, status, total_records, imported_by, created_at)
                    VALUES (:id, :client_id, :engagement_id, :name, :filename, 
                            :type, :status, :total, :user_id, :created)
                    RETURNING id
                """),
                {
                    "id": data_import_uuid,
                    "client_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),  # Demo account
                    "engagement_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),  # Demo engagement
                    "name": "Test Server Import",
                    "filename": "test_servers.csv",
                    "type": "cmdb",
                    "status": "processing",
                    "total": len(SAMPLE_CSV_DATA),
                    "user_id": demo_user,
                    "created": datetime.utcnow()
                }
            )
            data_import_id = result.scalar()
            logger.info(f"✅ Data import created with ID: {data_import_id}")
            
            # Create raw records
            for idx, record in enumerate(SAMPLE_CSV_DATA):
                await db.execute(
                    text("""
                        INSERT INTO raw_import_records
                        (id, data_import_id, client_account_id, engagement_id,
                         row_number, raw_data, is_processed, is_valid, created_at)
                        VALUES (:id, :import_id, :client_id, :engagement_id,
                                :row_num, :data, :processed, :valid, :created)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "import_id": data_import_id,
                        "client_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
                        "engagement_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
                        "row_num": idx + 1,  # Row numbers typically start at 1
                        "data": json.dumps(record),
                        "processed": False,
                        "valid": True,
                        "created": datetime.utcnow()
                    }
                )
            
            await db.commit()
            logger.info(f"✅ Data import created with {len(SAMPLE_CSV_DATA)} records")
        
        # Step 3: Create and link discovery flow
        logger.info("\n📋 Step 3: Creating discovery flow")
        async with AsyncSessionLocal() as db:
            # Create discovery flow record
            await db.execute(
                text("""
                    INSERT INTO discovery_flows
                    (id, flow_id, client_account_id, engagement_id, user_id,
                     data_import_id, flow_name, status, current_phase, created_at)
                    VALUES (:id, :flow_id, :client_id, :engagement_id, :user_id,
                            :import_id, :flow_name, :status, :phase, :created)
                    ON CONFLICT (flow_id) DO UPDATE
                    SET data_import_id = :import_id
                """),
                {
                    "id": str(uuid.uuid4()),  # Separate ID for the record
                    "flow_id": flow_id,
                    "client_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    "engagement_id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
                    "user_id": test_context.user_id,
                    "import_id": data_import_id,
                    "flow_name": "Simple E2E Test Discovery Flow",
                    "status": "initialized",
                    "phase": "initialization",
                    "created": datetime.utcnow()
                }
            )
            await db.commit()
            logger.info("✅ Discovery flow created and linked")
        
        await check_db_state("After Setup")
        
        # Step 4: Run discovery flow with phase controller
        logger.info("\n📋 Step 4: Running discovery flow phases")
        async with AsyncSessionLocal() as db:
            crewai_service = CrewAIFlowService(db)
            
            discovery_flow = create_unified_discovery_flow(
                flow_id=flow_id,
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                user_id=test_context.user_id,
                raw_data=SAMPLE_CSV_DATA,
                metadata={
                    "data_import_id": str(data_import_id)
                },
                crewai_service=crewai_service,
                context=test_context,
                master_flow_id=flow_id
            )
            
            phase_controller = PhaseController(discovery_flow)
            
            # Start execution
            result = await phase_controller.start_flow_execution()
            
            logger.info(f"\n📊 Execution Result:")
            logger.info(f"  - Current Phase: {result.phase.value}")
            logger.info(f"  - Status: {result.status}")
            logger.info(f"  - Requires User Input: {result.requires_user_input}")
            
            # Check if paused for approval
            if result.requires_user_input and result.phase == FlowPhase.FIELD_MAPPING_APPROVAL:
                logger.info("\n✅ Flow correctly paused for field mapping approval!")
                
                # Get field mappings
                field_mappings = {}
                if hasattr(discovery_flow.state, 'field_mappings'):
                    field_mappings = discovery_flow.state.field_mappings
                    logger.info("\n📊 Generated Field Mappings:")
                    for source, target in field_mappings.items():
                        if source != "confidence_scores":
                            logger.info(f"  - {source} → {target}")
                
                # Save field mappings to DB
                if data_import_id and field_mappings:
                    async with AsyncSessionLocal() as db2:
                        for source, target in field_mappings.items():
                            if source != "confidence_scores":
                                await db2.execute(
                                    text("""
                                        INSERT INTO import_field_mappings
                                        (id, data_import_id, client_account_id, source_field, 
                                         target_field, match_type, confidence_score, 
                                         status, created_at)
                                        VALUES (:id, :import_id, :client_id, :source, :target,
                                                :type, :confidence, :status, :created)
                                    """),
                                    {
                                        "id": str(uuid.uuid4()),
                                        "import_id": data_import_id,
                                        "client_id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
                                        "source": source,
                                        "target": target,
                                        "type": "auto_detected",
                                        "confidence": 0.8,
                                        "status": "suggested",
                                        "created": datetime.utcnow()
                                    }
                                )
                        await db2.commit()
                        logger.info(f"✅ Saved {len(field_mappings)-1} field mappings to database")
                
                await check_db_state("After Field Mapping")
                
                # Simulate approval
                logger.info("\n📋 Step 5: Simulating user approval")
                
                # Approve mappings in DB
                async with AsyncSessionLocal() as db2:
                    await db2.execute(
                        text("""
                            UPDATE import_field_mappings
                            SET status = 'approved', 
                                approved_by = :user_id,
                                approved_at = :now
                            WHERE data_import_id = :import_id
                        """),
                        {
                            "import_id": data_import_id,
                            "user_id": test_context.user_id,
                            "now": datetime.utcnow()
                        }
                    )
                    await db2.commit()
                    logger.info("✅ Field mappings approved")
                
                # Resume flow
                user_input = {
                    "approved_mappings": field_mappings,
                    "user_approval": True,
                    "approved_by": test_context.user_id
                }
                
                resume_result = await phase_controller.resume_flow_execution(
                    from_phase=FlowPhase.FIELD_MAPPING_APPROVAL,
                    user_input=user_input
                )
                
                logger.info(f"\n📊 Resume Result:")
                logger.info(f"  - Phase: {resume_result.phase.value}")
                logger.info(f"  - Status: {resume_result.status}")
                
                await check_db_state("After Resume")
                
                # Check for created assets
                async with AsyncSessionLocal() as db2:
                    # Check assets by discovery_flow_id reference
                    result = await db2.execute(
                        text("""
                            SELECT COUNT(*) FROM assets 
                            WHERE discovery_flow_id = :flow_id
                               OR master_flow_id = :flow_id
                        """),
                        {"flow_id": uuid.UUID(flow_id)}
                    )
                    asset_count = result.scalar()
                    logger.info(f"\n📊 Assets created: {asset_count}")
                    
                    # Get sample assets
                    if asset_count > 0:
                        asset_result = await db2.execute(
                            text("""
                                SELECT name, asset_type, ip_address, operating_system 
                                FROM assets 
                                WHERE discovery_flow_id = :flow_id
                                   OR master_flow_id = :flow_id
                                LIMIT 2
                            """),
                            {"flow_id": uuid.UUID(flow_id)}
                        )
                        for asset in asset_result:
                            logger.info(f"  - {asset.name}: {asset.asset_type} ({asset.ip_address})")
                
                logger.info("\n🎉 E2E Test completed successfully!")
            else:
                logger.error(f"\n❌ Flow did not pause at expected phase!")
                logger.error(f"  - Expected: field_mapping_approval")
                logger.error(f"  - Actual: {result.phase.value}")
                
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    from datetime import timedelta
    import sys
    
    # Add backend to path for imports
    sys.path.insert(0, '/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')
    
    asyncio.run(test_discovery_flow_simple())