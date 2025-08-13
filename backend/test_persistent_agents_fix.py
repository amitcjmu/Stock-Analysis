#!/usr/bin/env python3
"""
Test script to verify persistent agent creation fix
"""

import asyncio
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_persistent_agent_creation():
    """Test persistent agent creation with proper error handling"""

    try:
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        # Create test tenant identifiers
        client_id = str(uuid.uuid4())
        engagement_id = str(uuid.uuid4())

        logger.info(
            f"🧪 Testing persistent agent creation for tenant: {client_id[:8]}/{engagement_id[:8]}"
        )

        # Test 1: Initialize tenant pool
        logger.info("📋 Test 1: Initialize tenant pool")
        start_time = datetime.utcnow()

        try:
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                client_id, engagement_id
            )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"✅ Agent pool created successfully in {duration:.1f}ms")
            logger.info(f"   Agents created: {list(agent_pool.keys())}")

        except Exception as e:
            logger.error(f"❌ Failed to create agent pool: {e}")
            import traceback

            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return False

        # Test 2: Verify agent persistence
        logger.info("\n📋 Test 2: Verify agent persistence")
        start_time = datetime.utcnow()

        try:
            agent_pool_2 = await TenantScopedAgentPool.initialize_tenant_pool(
                client_id, engagement_id
            )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"✅ Agent pool retrieved successfully in {duration:.1f}ms")

            # Check if same agents are returned
            if agent_pool and agent_pool_2:
                for agent_type in agent_pool.keys():
                    if agent_type in agent_pool_2:
                        agent1_id = id(agent_pool[agent_type])
                        agent2_id = id(agent_pool_2[agent_type])
                        if agent1_id == agent2_id:
                            logger.info(
                                f"   ✅ {agent_type}: Same instance (persistence working)"
                            )
                        else:
                            logger.warning(
                                f"   ⚠️ {agent_type}: Different instance (not persistent)"
                            )

        except Exception as e:
            logger.error(f"❌ Failed to retrieve agent pool: {e}")
            return False

        # Test 3: Test multi-tenant isolation
        logger.info("\n📋 Test 3: Multi-tenant isolation")

        client_id_2 = str(uuid.uuid4())
        engagement_id_2 = str(uuid.uuid4())

        try:
            agent_pool_tenant2 = await TenantScopedAgentPool.initialize_tenant_pool(
                client_id_2, engagement_id_2
            )

            logger.info(
                f"✅ Second tenant pool created: {client_id_2[:8]}/{engagement_id_2[:8]}"
            )

            # Verify different agents for different tenants
            if agent_pool and agent_pool_tenant2:
                agent1 = agent_pool.get("data_analyst")
                agent2 = agent_pool_tenant2.get("data_analyst")

                if agent1 and agent2:
                    if id(agent1) != id(agent2):
                        logger.info(
                            "   ✅ Different agent instances for different tenants (isolation working)"
                        )
                    else:
                        logger.error(
                            "   ❌ Same agent instance for different tenants (isolation broken)"
                        )
                        return False

        except Exception as e:
            logger.error(f"❌ Failed multi-tenant test: {e}")
            return False

        logger.info("\n🎉 All tests passed successfully!")
        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("Make sure you're running this from the backend directory")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback

        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False


async def test_flow_execution_with_persistent_agents():
    """Test flow execution with persistent agents"""

    logger.info("\n📋 Test 4: Flow execution with persistent agents")

    try:
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.services.flow_orchestration.execution_engine_crew import (
            FlowCrewExecutor,
        )
        from app.core.context import RequestContext
        from sqlalchemy.ext.asyncio import AsyncSession
        from unittest.mock import MagicMock, AsyncMock

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

        # Create mock phase config
        phase_config = MagicMock()
        phase_config.name = "data_import"
        phase_config.crew_config = {"crew_factory": "test_factory"}

        # Create executor
        executor = FlowCrewExecutor(
            db=db_mock,
            context=context,
            master_repo=MagicMock(),
            flow_registry=MagicMock(),
            handler_registry=MagicMock(),
            validator_registry=MagicMock(),
        )

        logger.info(
            f"🔄 Testing discovery phase execution for tenant: {client_id[:8]}/{engagement_id[:8]}"
        )

        # Test discovery phase execution
        result = await executor._execute_discovery_phase(
            master_flow, phase_config, {"raw_data": []}
        )

        if result and result.get("status") != "failed":
            logger.info("✅ Discovery phase executed successfully")
            logger.info(f"   Result status: {result.get('status')}")
            logger.info(f"   Method used: {result.get('method')}")
        else:
            logger.error(f"❌ Discovery phase execution failed: {result.get('error')}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Flow execution test failed: {e}")
        import traceback

        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting persistent agent tests\n")

    # Run tests
    test1_success = await test_persistent_agent_creation()
    test2_success = await test_flow_execution_with_persistent_agents()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Summary:")
    logger.info(
        f"   Persistent Agent Creation: {'✅ Passed' if test1_success else '❌ Failed'}"
    )
    logger.info(
        f"   Flow Execution Integration: {'✅ Passed' if test2_success else '❌ Failed'}"
    )
    logger.info("=" * 50)

    return test1_success and test2_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
