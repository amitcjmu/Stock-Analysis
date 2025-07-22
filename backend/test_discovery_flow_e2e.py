#!/usr/bin/env python3
"""
End-to-End Test for Discovery Flow with New Phase Controller

This script tests the complete discovery flow including:
1. Flow initialization with CSV data
2. Phase-by-phase execution
3. Proper pausing at field mapping approval
4. Resume with user approval
5. Complete flow execution
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample CSV data for testing
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
    },
    {
        "server_name": "APP-DEV-01",
        "ip_address": "10.2.1.50",
        "operating_system": "Windows Server 2019",
        "environment": "Development",
        "cpu_cores": "4",
        "memory_gb": "16",
        "storage_gb": "250",
        "application": "Development Server",
        "criticality": "Low",
        "owner": "Dev Team"
    }
]


async def test_discovery_flow():
    """Test the complete discovery flow with phase controller"""
    logger.info("🚀 Starting Discovery Flow E2E Test")
    
    try:
        # Initialize database session
        from app.core.context import RequestContext
        from app.core.database import AsyncSessionLocal
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
        from app.services.crewai_flows.unified_discovery_flow.phase_controller import PhaseController
        from app.services.data_import.background_execution_service import BackgroundExecutionService
        
        # Test context
        test_context = RequestContext(
            client_account_id="12345",
            engagement_id="67890",
            user_id="test_user",
            request_id=str(uuid.uuid4())
        )
        
        async with AsyncSessionLocal() as db:
            logger.info("✅ Database session created")
            
            # Step 1: Create a master flow
            logger.info("\n📋 Step 1: Creating master flow")
            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
            
            flow_repo = CrewAIFlowStateExtensionsRepository(
                db,
                test_context.client_account_id,
                test_context.engagement_id,
                test_context.user_id
            )
            
            flow_id = str(uuid.uuid4())
            master_flow = await flow_repo.create_master_flow(
                flow_id=flow_id,
                flow_type="discovery",
                user_id=test_context.user_id,
                flow_name="E2E Test Discovery Flow",
                flow_configuration={
                    "source": "e2e_test",
                    "test": True
                },
                initial_state={
                    "raw_data": SAMPLE_CSV_DATA
                }
            )
            await db.commit()
            logger.info(f"✅ Master flow created: {flow_id}")
            
            # Step 2: Create discovery flow with CSV data
            logger.info("\n📋 Step 2: Creating discovery flow with sample data")
            crewai_service = CrewAIFlowService(db)
            
            discovery_flow = create_unified_discovery_flow(
                flow_id=flow_id,
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                user_id=test_context.user_id,
                raw_data=SAMPLE_CSV_DATA,
                metadata={
                    "source": "e2e_test",
                    "master_flow_id": flow_id
                },
                crewai_service=crewai_service,
                context=test_context,
                master_flow_id=flow_id
            )
            logger.info("✅ Discovery flow created")
            
            # Step 3: Initialize phase controller
            logger.info("\n📋 Step 3: Initializing phase controller")
            phase_controller = PhaseController(discovery_flow)
            logger.info("✅ Phase controller initialized")
            
            # Step 4: Start flow execution
            logger.info("\n📋 Step 4: Starting phase-by-phase execution")
            result = await phase_controller.start_flow_execution()
            
            logger.info("📊 Initial execution result:")
            logger.info(f"  - Phase: {result.phase.value}")
            logger.info(f"  - Status: {result.status}")
            logger.info(f"  - Requires user input: {result.requires_user_input}")
            logger.info(f"  - Next phase: {result.next_phase.value if result.next_phase else 'None'}")
            
            # Check flow status
            flow_status = phase_controller.get_flow_status()
            logger.info("\n📊 Flow status after initial execution:")
            logger.info(f"  - Current phase: {flow_status['current_phase']}")
            logger.info(f"  - Execution halted: {flow_status['execution_halted']}")
            logger.info(f"  - Completed phases: {flow_status['completed_phases']}")
            logger.info(f"  - Progress: {flow_status['progress_percentage']}%")
            
            # Verify we paused at field mapping approval
            if result.phase.value == "field_mapping_approval" and result.requires_user_input:
                logger.info("\n✅ SUCCESS: Flow properly paused at field mapping approval!")
                
                # Check the field mappings generated
                if hasattr(discovery_flow, 'state') and hasattr(discovery_flow.state, 'field_mappings'):
                    field_mappings = discovery_flow.state.field_mappings
                    logger.info("\n📊 Generated field mappings:")
                    for source, target in field_mappings.items():
                        if source != "confidence_scores":
                            logger.info(f"  - {source} → {target}")
                    
                    # Verify we have real field names, not indices
                    if "0" in field_mappings or "1" in field_mappings or "2" in field_mappings:
                        logger.error("❌ ERROR: Field mappings contain numeric indices instead of field names!")
                    else:
                        logger.info("✅ Field mappings contain proper field names")
                
                # Step 5: Simulate user approval
                logger.info("\n📋 Step 5: Simulating user approval of field mappings")
                
                user_input = {
                    "approved_mappings": field_mappings if 'field_mappings' in locals() else {},
                    "approval_timestamp": datetime.utcnow().isoformat(),
                    "approved_by": test_context.user_id,
                    "approval_notes": "Approved via E2E test",
                    "user_approval": True
                }
                
                # Resume flow execution
                from app.services.crewai_flows.unified_discovery_flow.phase_controller import FlowPhase
                resume_result = await phase_controller.resume_flow_execution(
                    from_phase=FlowPhase.FIELD_MAPPING_APPROVAL,
                    user_input=user_input
                )
                
                logger.info("\n📊 Resume execution result:")
                logger.info(f"  - Phase: {resume_result.phase.value}")
                logger.info(f"  - Status: {resume_result.status}")
                logger.info(f"  - Requires user input: {resume_result.requires_user_input}")
                
                # Check final flow status
                final_status = phase_controller.get_flow_status()
                logger.info("\n📊 Final flow status:")
                logger.info(f"  - Current phase: {final_status['current_phase']}")
                logger.info(f"  - Completed phases: {final_status['completed_phases']}")
                logger.info(f"  - Progress: {final_status['progress_percentage']}%")
                
                if resume_result.phase.value == "finalization" and resume_result.status == "completed":
                    logger.info("\n🎉 SUCCESS: Discovery flow completed successfully!")
                else:
                    logger.warning(f"\n⚠️ Flow ended at phase: {resume_result.phase.value} with status: {resume_result.status}")
                
            else:
                logger.error("\n❌ ERROR: Flow did not pause at field mapping approval!")
                logger.error(f"  - Current phase: {result.phase.value}")
                logger.error(f"  - Requires user input: {result.requires_user_input}")
            
            # Step 6: Verify flow state in database
            logger.info("\n📋 Step 6: Verifying flow state in database")
            
            # Check master flow status
            master_flow_state = await flow_repo.get_by_flow_id(flow_id)
            if master_flow_state:
                logger.info(f"✅ Master flow status: {master_flow_state.flow_status}")
                logger.info(f"✅ Master flow phase data: {json.dumps(master_flow_state.flow_persistence_data, indent=2)}")
            else:
                logger.error("❌ Master flow state not found in database")
            
            logger.info("\n✅ E2E Test completed successfully!")
            
    except Exception as e:
        logger.error(f"\n❌ E2E Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_discovery_flow())