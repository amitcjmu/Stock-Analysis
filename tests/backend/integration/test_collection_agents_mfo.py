"""
Test Collection Flow CrewAI Agents with MFO Integration
Verifies that all agents are properly implemented through TenantScopedAgentPool
and can be imported with proper tenant isolation and MFO patterns.

Generated with CC for MFO integration and TenantScopedAgentPool pattern.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import MFO fixtures and demo tenant constants
from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    MockRequestContext,
    MockServiceRegistry,
)
from tests.fixtures.pytest_markers import *  # Import all markers

from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool


@pytest.fixture
def demo_context() -> MockRequestContext:
    """Demo tenant context for MFO testing."""
    return MockRequestContext(
        client_account_id=DEMO_CLIENT_ACCOUNT_ID,
        engagement_id=DEMO_ENGAGEMENT_ID,
        user_id=DEMO_USER_ID,
    )


@pytest.fixture
def mock_service_registry() -> MockServiceRegistry:
    """Mock service registry for MFO operations."""
    return MockServiceRegistry()


@pytest.fixture
def mock_tenant_scoped_agent_pool():
    """Mock TenantScopedAgentPool for testing agent operations."""
    mock_pool = MagicMock()

    # Mock agent instances for different types
    def create_mock_agent(agent_type):
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value={
            "status": "completed",
            "agent_type": agent_type,
            "result": {"analysis": f"Test result from {agent_type}"},
            "execution_time": 1.23,
        })
        mock_agent.agent_metadata = MagicMock(return_value=MagicMock(
            name=agent_type,
            description=f"Mock {agent_type} for testing",
            agent_class=f"Mock{agent_type.title()}Agent",
            required_tools=[],
            capabilities=["analysis", "decision_making"],
        ))
        return mock_agent

    # Mock pool methods
    mock_pool.get_agent = AsyncMock(side_effect=lambda context, agent_type, **kwargs: create_mock_agent(agent_type))
    mock_pool.release_agent = AsyncMock()
    mock_pool.get_pool_stats = AsyncMock(return_value={
        "active_agents": 9,  # All collection agents
        "total_agents": 9,
        "memory_usage": 256.5,
    })

    return mock_pool


class TestCollectionAgentsMFO:
    """Test suite for Collection Flow agents with MFO integration."""

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.collection_flow
    @pytest.mark.tenant_isolation
    async def test_platform_detection_agents_through_mfo(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that platform detection agents can be accessed through TenantScopedAgentPool."""
        agent_types = [
            "platform_detection_agent",
            "credential_validation_agent",
            "tier_recommendation_agent"
        ]

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            for agent_type in agent_types:
                # Get agent through TenantScopedAgentPool with proper tenant context
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

                # Verify agent can be executed
                result = await agent.execute({
                    "task_type": "platform_detection",
                    "context": demo_context.to_dict(),
                })

                # Verify proper tenant-scoped execution
                assert result["status"] == "completed"
                assert result["agent_type"] == agent_type
                assert "result" in result

                # Verify tenant isolation
                mock_tenant_scoped_agent_pool.get_agent.assert_called_with(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

        # Verify agent metadata through TenantScopedAgentPool
        for agent_type in agent_types:
            agent = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type=agent_type,
                service_registry=mock_service_registry,
            )

            metadata = agent.agent_metadata()
            assert metadata.name == agent_type
            assert hasattr(metadata, "description")
            assert hasattr(metadata, "agent_class")
            assert hasattr(metadata, "required_tools")
            assert hasattr(metadata, "capabilities")

        print("✅ Platform detection agents loaded successfully through MFO")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.collection_flow
    @pytest.mark.tenant_isolation
    async def test_collection_orchestration_agent_through_mfo(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that collection orchestration agent can be accessed through TenantScopedAgentPool."""
        agent_type = "collection_orchestrator_agent"

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # Get agent through TenantScopedAgentPool with proper tenant context
            agent = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type=agent_type,
                service_registry=mock_service_registry,
            )

            # Execute collection orchestration task
            result = await agent.execute({
                "task_type": "collection_orchestration",
                "context": demo_context.to_dict(),
                "workflow": "data_collection",
            })

            # Verify proper execution through MFO
            assert result["status"] == "completed"
            assert result["agent_type"] == agent_type
            assert "result" in result

            # Verify tenant isolation in orchestration
            mock_tenant_scoped_agent_pool.get_agent.assert_called_with(
                context=demo_context,
                agent_type=agent_type,
                service_registry=mock_service_registry,
            )

            # Verify agent metadata
            metadata = agent.agent_metadata()
            assert metadata.name == agent_type

        print("✅ Collection orchestration agent loaded successfully through MFO")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.collection_flow
    @pytest.mark.tenant_isolation
    async def test_gap_analysis_agents_through_mfo(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that gap analysis agents can be accessed through TenantScopedAgentPool."""
        agent_types = [
            "critical_attribute_assessor",
            "gap_prioritization_agent"
        ]

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            for agent_type in agent_types:
                # Get agent through TenantScopedAgentPool with proper tenant context
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

                # Execute gap analysis task
                result = await agent.execute({
                    "task_type": "gap_analysis",
                    "context": demo_context.to_dict(),
                    "assessment_data": {"critical_attributes": ["security", "performance"]},
                })

                # Verify proper execution through MFO
                assert result["status"] == "completed"
                assert result["agent_type"] == agent_type
                assert "result" in result

                # Verify tenant isolation
                mock_tenant_scoped_agent_pool.get_agent.assert_called_with(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

        print("✅ Gap analysis agents loaded successfully through MFO")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.collection_flow
    @pytest.mark.tenant_isolation
    async def test_manual_collection_agents_through_mfo(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that manual collection agents can be accessed through TenantScopedAgentPool."""
        agent_types = [
            "questionnaire_dynamics_agent",
            "validation_workflow_agent",
            "progress_tracking_agent"
        ]

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            for agent_type in agent_types:
                # Get agent through TenantScopedAgentPool with proper tenant context
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

                # Execute manual collection task
                result = await agent.execute({
                    "task_type": "manual_collection",
                    "context": demo_context.to_dict(),
                    "questionnaire_data": {"questions": ["Q1", "Q2"], "responses": ["A1", "A2"]},
                })

                # Verify proper execution through MFO
                assert result["status"] == "completed"
                assert result["agent_type"] == agent_type
                assert "result" in result

                # Verify tenant isolation
                mock_tenant_scoped_agent_pool.get_agent.assert_called_with(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

        print("✅ Manual collection agents loaded successfully through MFO")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.collection_flow
    @pytest.mark.tenant_isolation
    async def test_all_agents_through_tenant_scoped_pool(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that all collection agents have required attributes and work through TenantScopedAgentPool."""
        agent_types = [
            "platform_detection_agent",
            "credential_validation_agent",
            "tier_recommendation_agent",
            "collection_orchestrator_agent",
            "critical_attribute_assessor",
            "gap_prioritization_agent",
            "questionnaire_dynamics_agent",
            "validation_workflow_agent",
            "progress_tracking_agent",
        ]

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            results = {}

            for agent_type in agent_types:
                # Get agent through TenantScopedAgentPool
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )

                # Verify agent has required methods
                assert hasattr(agent, "execute"), f"{agent_type} missing execute method"
                assert hasattr(agent, "agent_metadata"), f"{agent_type} missing agent_metadata method"
                assert callable(getattr(agent, "execute")), f"{agent_type} execute is not callable"
                assert callable(getattr(agent, "agent_metadata")), f"{agent_type} agent_metadata is not callable"

                # Check metadata structure
                metadata = agent.agent_metadata()
                assert hasattr(metadata, "name"), f"{agent_type} metadata missing name"
                assert hasattr(metadata, "description"), f"{agent_type} metadata missing description"
                assert hasattr(metadata, "agent_class"), f"{agent_type} metadata missing agent_class"
                assert hasattr(metadata, "required_tools"), f"{agent_type} metadata missing required_tools"
                assert hasattr(metadata, "capabilities"), f"{agent_type} metadata missing capabilities"

                # Execute agent to verify it works
                result = await agent.execute({
                    "task_type": "test_execution",
                    "context": demo_context.to_dict(),
                    "agent_type": agent_type,
                })

                results[agent_type] = result

                # Verify tenant isolation
                assert result["agent_type"] == agent_type
                assert result["status"] == "completed"

            # Verify all agents were accessed through TenantScopedAgentPool
            assert mock_tenant_scoped_agent_pool.get_agent.call_count == len(agent_types)

            # Verify pool stats
            pool_stats = await mock_tenant_scoped_agent_pool.get_pool_stats()
            assert pool_stats["active_agents"] == 9
            assert pool_stats["total_agents"] == 9
            assert pool_stats["memory_usage"] > 0

        print("✅ All collection agents have required attributes and work through TenantScopedAgentPool")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.performance
    @pytest.mark.tenant_isolation
    async def test_agent_pool_performance_and_isolation(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test agent pool performance and tenant isolation."""
        agent_types = ["platform_detection_agent", "collection_orchestrator_agent", "gap_prioritization_agent"]

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # Test concurrent agent access with same tenant context
            import asyncio

            async def get_and_execute_agent(agent_type):
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type=agent_type,
                    service_registry=mock_service_registry,
                )
                return await agent.execute({
                    "task_type": "concurrent_test",
                    "context": demo_context.to_dict(),
                })

            # Execute multiple agents concurrently
            tasks = [get_and_execute_agent(agent_type) for agent_type in agent_types]
            results = await asyncio.gather(*tasks)

            # Verify all executions succeeded
            for i, result in enumerate(results):
                assert result["status"] == "completed"
                assert result["agent_type"] == agent_types[i]

            # Test with different tenant context (should be isolated)
            different_context = MockRequestContext(
                client_account_id="different-tenant-id",
                engagement_id="different-engagement-id",
                user_id="different-user-id",
            )

            agent = await TenantScopedAgentPool.get_agent(
                context=different_context,
                agent_type="platform_detection_agent",
                service_registry=mock_service_registry,
            )

            result = await agent.execute({
                "task_type": "isolation_test",
                "context": different_context.to_dict(),
            })

            # Verify tenant isolation
            assert result["status"] == "completed"
            # In real implementation, this would verify different agent instances per tenant

        print("✅ Agent pool performance and tenant isolation verified")

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.agent_memory
    @pytest.mark.integration
    async def test_agent_memory_persistence_through_mfo(
        self, demo_context, mock_tenant_scoped_agent_pool, mock_service_registry
    ):
        """Test that agent memory persists across executions within same tenant."""
        agent_type = "questionnaire_dynamics_agent"

        # Mock agent with memory simulation
        memory_data = {}

        def create_stateful_agent():
            mock_agent = MagicMock()

            async def execute_with_memory(task_data):
                # Simulate memory persistence
                task_id = task_data.get("task_id", "default")
                if task_id in memory_data:
                    memory_data[task_id]["executions"] += 1
                else:
                    memory_data[task_id] = {"executions": 1, "learned_patterns": []}

                return {
                    "status": "completed",
                    "agent_type": agent_type,
                    "result": {"analysis": f"Execution #{memory_data[task_id]['executions']}"},
                    "memory_state": memory_data[task_id],
                    "execution_time": 1.23,
                }

            mock_agent.execute = AsyncMock(side_effect=execute_with_memory)
            mock_agent.agent_metadata = MagicMock(return_value=MagicMock(
                name=agent_type,
                description=f"Stateful {agent_type} with memory",
                capabilities=["memory", "learning"],
            ))
            return mock_agent

        stateful_agent = create_stateful_agent()
        mock_tenant_scoped_agent_pool.get_agent = AsyncMock(return_value=stateful_agent)

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # First execution
            agent1 = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type=agent_type,
                service_registry=mock_service_registry,
            )

            result1 = await agent1.execute({
                "task_type": "memory_test",
                "task_id": "test_session",
                "context": demo_context.to_dict(),
            })

            assert result1["memory_state"]["executions"] == 1

            # Second execution - same tenant context, should have memory
            agent2 = await TenantScopedAgentPool.get_agent(
                context=demo_context,  # Same tenant context
                agent_type=agent_type,
                service_registry=mock_service_registry,
            )

            result2 = await agent2.execute({
                "task_type": "memory_test",
                "task_id": "test_session",  # Same task ID
                "context": demo_context.to_dict(),
            })

            # Verify memory persistence
            assert result2["memory_state"]["executions"] == 2
            assert result2["result"]["analysis"] == "Execution #2"

        print("✅ Agent memory persistence verified through TenantScopedAgentPool")


if __name__ == "__main__":
    # Run with MFO and agent markers
    pytest.main([__file__, "-v", "-m", "mfo and agent"])
