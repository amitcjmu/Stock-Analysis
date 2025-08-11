#!/usr/bin/env python3
"""
Test script to verify ADR-015 compliance - NO FALLBACK to service pattern
"""

import asyncio
import logging
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_no_fallback_pattern():
    """Test that the system properly fails without fallback when agents aren't available"""

    logger.info("🧪 Testing ADR-015 compliance - No fallback to service pattern")

    try:
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.services.flow_orchestration.execution_engine_crew import (
            FlowCrewExecutor,
        )
        from app.core.context import RequestContext
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock objects
        db_mock = AsyncMock(spec=AsyncSession)

        # Create test context
        client_id = str(uuid.uuid4())
        engagement_id = str(uuid.uuid4())

        context = RequestContext(
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
        )

        # Create mock flow
        master_flow = CrewAIFlowStateExtensions()
        master_flow.client_account_id = client_id
        master_flow.engagement_id = engagement_id
        master_flow.user_id = context.user_id
        master_flow.flow_id = context.flow_id
        master_flow.flow_type = "discovery"

        # Create executor
        executor = FlowCrewExecutor(
            db=db_mock,
            context=context,
            master_repo=MagicMock(),
            flow_registry=MagicMock(),
            handler_registry=MagicMock(),
            validator_registry=MagicMock(),
        )

        logger.info("📋 Test 1: Discovery Phase Execution")

        # Test discovery phase
        phase_config = MagicMock()
        phase_config.name = "data_import"
        phase_config.crew_config = {"crew_factory": "test_factory"}

        result = await executor._execute_discovery_phase(
            master_flow, phase_config, {"raw_data": []}
        )

        # Check the result
        if result.get("method") == "persistent_agent_failure":
            logger.info("✅ Discovery phase correctly failed without fallback")
            logger.info(f"   Error type: {result.get('details', {}).get('error_type')}")
            logger.info(f"   Message: {result.get('details', {}).get('message')}")
            assert "ADR-015" in str(result.get("details", {}).get("error_type"))
        else:
            logger.error(f"❌ Unexpected result method: {result.get('method')}")
            return False

        logger.info("\n📋 Test 2: Assessment Phase Execution")

        # Test assessment phase
        phase_config.name = "risk_assessment"

        result = await executor._execute_assessment_phase(
            master_flow, phase_config, {"items": []}
        )

        if result.get("method") == "persistent_agent_failure":
            logger.info("✅ Assessment phase correctly failed without fallback")
            assert "ADR-015" in str(result.get("details", {}).get("error_type"))
        else:
            logger.error(f"❌ Unexpected result method: {result.get('method')}")
            return False

        logger.info("\n📋 Test 3: Collection Phase Execution")

        # Test collection phase
        phase_config.name = "platform_detection"
        phase_config.crew_config = {
            "crew_factory": "create_platform_detection_crew",
            "input_mapping": {},
            "output_mapping": {},
        }

        result = await executor._execute_collection_phase(
            master_flow, phase_config, {"infrastructure_data": {}}
        )

        if result.get("method") == "persistent_agent_failure":
            logger.info("✅ Collection phase correctly failed without fallback")
            assert "ADR-015" in str(result.get("details", {}).get("error_type"))
        else:
            logger.error(f"❌ Unexpected result method: {result.get('method')}")
            return False

        logger.info("\n🎉 All tests passed - System correctly fails without fallback!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback

        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False


async def test_no_service_instantiation():
    """Test that CrewAIFlowService is never instantiated"""

    logger.info("\n📋 Test 4: Verify no CrewAIFlowService instantiation")

    try:
        # Check that CrewAIFlowService is not imported in execution_engine_crew
        import ast
        import inspect
        from app.services.flow_orchestration.execution_engine_crew import (
            FlowCrewExecutor,
        )

        # Get the source code
        source_file = inspect.getfile(FlowCrewExecutor)
        with open(source_file, "r") as f:
            source_code = f.read()

        # Parse the AST
        tree = ast.parse(source_code)

        # Check for CrewAIFlowService references
        crewai_service_found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "CrewAIFlowService":
                crewai_service_found = True
                break
            if isinstance(node, ast.ImportFrom):
                if hasattr(node, "module") and "crewai_flow_service" in str(
                    node.module
                ):
                    crewai_service_found = True
                    break

        if not crewai_service_found:
            logger.info("✅ No CrewAIFlowService references found in code")
            return True
        else:
            logger.error("❌ CrewAIFlowService references still exist in code")
            return False

    except Exception as e:
        logger.error(f"❌ Service instantiation test failed: {e}")
        return False


async def main():
    """Run all ADR-015 compliance tests"""
    logger.info("🚀 Starting ADR-015 Compliance Tests\n")

    # Run tests
    test1_success = await test_no_fallback_pattern()
    test2_success = await test_no_service_instantiation()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 ADR-015 Compliance Test Summary:")
    logger.info(
        f"   No Fallback Pattern: {'✅ Passed' if test1_success else '❌ Failed'}"
    )
    logger.info(
        f"   No Service Instantiation: {'✅ Passed' if test2_success else '❌ Failed'}"
    )
    logger.info("=" * 50)

    if test1_success and test2_success:
        logger.info("\n✅ SYSTEM IS ADR-015 COMPLIANT")
        logger.info("   - No fallback to service pattern")
        logger.info("   - Persistent agents are mandatory")
        logger.info("   - System fails fast when agents unavailable")
    else:
        logger.error("\n❌ SYSTEM VIOLATES ADR-015")

    return test1_success and test2_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
