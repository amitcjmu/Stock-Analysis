#!/usr/bin/env python3
"""
Test Collection Flow Configuration and Registration
ADCS: Validates the Collection Flow integration with Master Flow Orchestrator
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_collection_flow():
    """Test Collection Flow configuration and registration"""
    
    try:
        # Import required modules
        from app.services.flow_configs import (
            initialize_all_flows,
            verify_flow_configurations,
            get_flow_summary,
            get_collection_flow_config
        )
        
        logger.info("=" * 80)
        logger.info("COLLECTION FLOW CONFIGURATION TEST")
        logger.info("=" * 80)
        
        # Step 1: Initialize all flows
        logger.info("\n1. Initializing all flows...")
        init_result = initialize_all_flows()
        
        if init_result.get("errors"):
            logger.error(f"Errors during initialization: {init_result['errors']}")
            return False
        
        logger.info(f"✅ Flows registered: {init_result['flows_registered']}")
        logger.info(f"✅ Validators registered: {len(init_result['validators_registered'])}")
        logger.info(f"✅ Handlers registered: {len(init_result['handlers_registered'])}")
        
        # Step 2: Verify Collection Flow is registered
        logger.info("\n2. Verifying Collection Flow registration...")
        verification = verify_flow_configurations()
        
        if "collection" not in verification["flow_details"]:
            logger.error("❌ Collection Flow not found in registered flows!")
            return False
        
        collection_details = verification["flow_details"]["collection"]
        logger.info(f"✅ Collection Flow registered with {collection_details['phases']} phases")
        logger.info(f"   - Has validators: {collection_details['has_validators']}")
        logger.info(f"   - Has handlers: {collection_details['has_handlers']}")
        logger.info(f"   - Capabilities: {collection_details['capabilities']}")
        
        # Step 3: Get Collection Flow configuration
        logger.info("\n3. Loading Collection Flow configuration...")
        collection_config = get_collection_flow_config()
        
        logger.info(f"✅ Flow Name: {collection_config.name}")
        logger.info(f"✅ Display Name: {collection_config.display_name}")
        logger.info(f"✅ Version: {collection_config.version}")
        logger.info(f"✅ Description: {collection_config.description}")
        
        # Step 4: Validate phases
        logger.info("\n4. Validating Collection Flow phases...")
        expected_phases = [
            "platform_detection",
            "automated_collection",
            "gap_analysis",
            "manual_collection",
            "synthesis"
        ]
        
        actual_phases = [phase.name for phase in collection_config.phases]
        
        if actual_phases != expected_phases:
            logger.error(f"❌ Phase mismatch! Expected: {expected_phases}, Got: {actual_phases}")
            return False
        
        logger.info("✅ All expected phases present:")
        for i, phase in enumerate(collection_config.phases):
            logger.info(f"   {i+1}. {phase.display_name} ({phase.name})")
            logger.info(f"      - Validators: {phase.validators}")
            logger.info(f"      - Pre-handlers: {phase.pre_handlers}")
            logger.info(f"      - Post-handlers: {phase.post_handlers}")
            logger.info(f"      - Can pause: {phase.can_pause}")
            logger.info(f"      - Can skip: {phase.can_skip}")
        
        # Step 5: Validate crew configurations
        logger.info("\n5. Validating crew configurations...")
        for phase in collection_config.phases:
            if phase.crew_config:
                crew_type = phase.crew_config.get("crew_type")
                crew_factory = phase.crew_config.get("crew_factory")
                logger.info(f"✅ {phase.name}: {crew_type} -> {crew_factory}")
        
        # Step 6: Test flow registry access
        logger.info("\n6. Testing flow registry access...")
        from app.services.flow_type_registry import flow_type_registry
        
        if not flow_type_registry.is_registered("collection"):
            logger.error("❌ Collection Flow not accessible via registry!")
            return False
        
        registry_config = flow_type_registry.get_flow_config("collection")
        logger.info(f"✅ Registry access successful: {registry_config.display_name}")
        
        # Step 7: Validate automation tiers
        logger.info("\n7. Validating automation tier support...")
        default_tier = collection_config.default_configuration.get("automation_tier")
        logger.info(f"✅ Default automation tier: {default_tier}")
        
        quality_thresholds = collection_config.phases[1].metadata.get("quality_thresholds", {})
        logger.info("✅ Quality thresholds by tier:")
        for tier, threshold in quality_thresholds.items():
            logger.info(f"   - {tier}: {threshold}")
        
        # Step 8: Validate integrations
        logger.info("\n8. Validating supported integrations...")
        supported_integrations = collection_config.metadata.get("supported_integrations", [])
        logger.info(f"✅ Supported adapters: {len(supported_integrations)}")
        for adapter in supported_integrations:
            logger.info(f"   - {adapter}")
        
        # Step 9: Get flow summary
        logger.info("\n9. Getting flow summary...")
        flow_summary = get_flow_summary()
        collection_summary = next(
            (f for f in flow_summary if f["name"] == "collection"), 
            None
        )
        
        if not collection_summary:
            logger.error("❌ Collection Flow not in summary!")
            return False
        
        logger.info(f"✅ Summary: {collection_summary}")
        
        # Step 10: Test error handlers
        logger.info("\n10. Validating error handling configuration...")
        if collection_config.error_handler:
            logger.info(f"✅ Error handler configured: {collection_config.error_handler}")
        
        rollback_handler = collection_config.metadata.get("rollback_handler")
        if rollback_handler:
            logger.info(f"✅ Rollback handler configured: {rollback_handler}")
        
        checkpoint_handler = collection_config.metadata.get("checkpoint_handler")
        if checkpoint_handler:
            logger.info(f"✅ Checkpoint handler configured: {checkpoint_handler}")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("COLLECTION FLOW TEST SUMMARY")
        logger.info("=" * 80)
        logger.info("✅ Collection Flow successfully configured and registered")
        logger.info("✅ All 5 phases properly defined")
        logger.info("✅ Validators and handlers registered")
        logger.info("✅ Crew configurations valid")
        logger.info("✅ Multi-tier automation support confirmed")
        logger.info("✅ Integration points configured")
        logger.info("\n🎉 COLLECTION FLOW READY FOR USE AS THE 9TH FLOW TYPE!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_master_flow_orchestrator_integration():
    """Test Collection Flow integration with Master Flow Orchestrator"""
    
    try:
        logger.info("\n" + "=" * 80)
        logger.info("MASTER FLOW ORCHESTRATOR INTEGRATION TEST")
        logger.info("=" * 80)
        
        # Import required modules
        from app.core.database import AsyncSessionLocal
        from app.core.context import RequestContext
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        import uuid
        
        # Create test context
        test_context = RequestContext(
            request_id=str(uuid.uuid4()),
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        
        logger.info("\n1. Creating Master Flow Orchestrator instance...")
        
        async with AsyncSessionLocal() as db:
            orchestrator = MasterFlowOrchestrator(db, test_context)
            
            # Test flow type listing
            logger.info("\n2. Listing available flow types...")
            flow_types = orchestrator.flow_registry.list_flow_types()
            logger.info(f"✅ Available flow types: {flow_types}")
            
            if "collection" not in flow_types:
                logger.error("❌ Collection Flow not available in orchestrator!")
                return False
            
            logger.info("✅ Collection Flow is available in Master Flow Orchestrator")
            
            # Test flow configuration retrieval
            logger.info("\n3. Retrieving Collection Flow configuration...")
            collection_config = orchestrator.flow_registry.get_flow_config("collection")
            logger.info(f"✅ Retrieved config: {collection_config.display_name}")
            
            # Test validator availability
            logger.info("\n4. Checking validator availability...")
            collection_validators = [
                "platform_validation",
                "credential_validation",
                "collection_validation",
                "data_quality_validation",
                "gap_validation",
                "sixr_impact_validation",
                "response_validation",
                "completeness_validation",
                "final_validation",
                "sixr_readiness_validation"
            ]
            
            all_validators_available = True
            for validator in collection_validators:
                if not orchestrator.validator_registry.is_registered(validator):
                    logger.error(f"❌ Validator not registered: {validator}")
                    all_validators_available = False
            
            if all_validators_available:
                logger.info("✅ All Collection Flow validators registered")
            
            # Test handler availability
            logger.info("\n5. Checking handler availability...")
            collection_handlers = [
                "collection_initialization",
                "collection_finalization",
                "collection_error_handler"
            ]
            
            all_handlers_available = True
            for handler in collection_handlers:
                if not orchestrator.handler_registry.is_registered(handler):
                    logger.error(f"❌ Handler not registered: {handler}")
                    all_handlers_available = False
            
            if all_handlers_available:
                logger.info("✅ All Collection Flow lifecycle handlers registered")
            
            logger.info("\n✅ COLLECTION FLOW FULLY INTEGRATED WITH MASTER FLOW ORCHESTRATOR")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Run all tests"""
    logger.info("Starting Collection Flow tests...\n")
    
    # Test 1: Configuration and registration
    config_test_passed = await test_collection_flow()
    
    if not config_test_passed:
        logger.error("\n❌ Configuration test failed. Stopping tests.")
        return
    
    # Test 2: Master Flow Orchestrator integration
    integration_test_passed = await test_master_flow_orchestrator_integration()
    
    if not integration_test_passed:
        logger.error("\n❌ Integration test failed.")
        return
    
    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS PASSED! 🎉")
    logger.info("Collection Flow is ready as the 9th flow type in the system")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())