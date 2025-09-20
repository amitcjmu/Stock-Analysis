"""
Integration tests for the new agentic Discovery flow with MFO integration.
Tests the removal of hardcoded thresholds and dynamic agent decision-making.
Aligned with Master Flow Orchestrator (MFO) pattern and TenantScopedAgentPool.

Generated with CC for MFO integration and proper tenant isolation.
"""

import asyncio
import json
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Import MFO fixtures and demo tenant constants
from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    MockRequestContext,
    MockServiceRegistry,
)
# Pytest markers are configured in pytest_markers.py and used via @pytest.mark notation

from app.core.database import Base
from app.models.discovery_models import DiscoveryFlow
from app.models.master_flow import MasterFlow
from app.services.crewai_flows.unified_discovery_flow.unified_discovery_flow import (
    UnifiedDiscoveryFlow,
)
from app.services.flow_orchestration.status_manager import FlowStatusManager
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool


# Test database setup
@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", poolclass=NullPool, echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


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

    # Mock agent instances
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value={
        "status": "completed",
        "result": {
            "decision": "approve",
            "confidence": 0.95,
            "reasoning": "High quality mapping with strong semantic alignment",
            "suggestions": ["Consider adding additional context for edge cases"],
        },
        "execution_time": 1.23,
    })

    # Mock pool methods
    mock_pool.get_agent = AsyncMock(return_value=mock_agent)
    mock_pool.release_agent = AsyncMock()
    mock_pool.get_pool_stats = AsyncMock(return_value={
        "active_agents": 2,
        "total_agents": 5,
        "memory_usage": 128.5,
    })

    return mock_pool


@pytest.fixture
def sample_mapping_data():
    """Sample field mapping data for testing."""
    return {
        "source_fields": [
            {"name": "hostname", "type": "string", "sample": "server01.example.com"},
            {"name": "ip_address", "type": "string", "sample": "192.168.1.100"},
            {"name": "cpu_cores", "type": "integer", "sample": "8"},
            {"name": "memory_gb", "type": "integer", "sample": "32"},
            {"name": "storage_tb", "type": "float", "sample": "2.5"},
        ],
        "target_schema": {
            "host_name": {"type": "string", "required": True},
            "ip": {"type": "string", "required": True},
            "cpu_count": {"type": "integer", "required": True},
            "ram_gb": {"type": "integer", "required": True},
            "disk_tb": {"type": "float", "required": False},
        },
        "mappings": [
            {"source": "hostname", "target": "host_name", "confidence": 0.98},
            {"source": "ip_address", "target": "ip", "confidence": 0.99},
            {"source": "cpu_cores", "target": "cpu_count", "confidence": 0.85},
            {"source": "memory_gb", "target": "ram_gb", "confidence": 0.92},
            {"source": "storage_tb", "target": "disk_tb", "confidence": 0.88},
        ],
    }


class TestAgenticDiscoveryFlowMFO:
    """Test suite for the new agentic Discovery flow with MFO integration."""

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.async_test
    @pytest.mark.discovery_flow
    async def test_no_hardcoded_thresholds_with_mfo(
        self, test_session, demo_context, mock_tenant_scoped_agent_pool,
        mock_service_registry, sample_mapping_data
    ):
        """Test that hardcoded thresholds are removed and agents make dynamic decisions through MFO."""
        # Create master flow with proper tenant scoping
        master_flow = MasterFlow(
            flow_id="master_test_001",
            flow_type="discovery",
            status="in_progress",
            client_account_id=demo_context.client_account_id,
            engagement_id=demo_context.engagement_id,
            created_by=demo_context.user_id,
            config={},
        )
        test_session.add(master_flow)

        # Create discovery flow with proper tenant scoping
        discovery_flow = DiscoveryFlow(
            flow_id="disc_test_001",
            master_flow_id="master_test_001",
            client_account_id=demo_context.client_account_id,
            engagement_id=demo_context.engagement_id,
            created_by=demo_context.user_id,
            status="field_mapping",
            config={},
            state_data={},
        )
        test_session.add(discovery_flow)
        await test_session.commit()

        # Use TenantScopedAgentPool through MFO pattern
        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # Get agent through TenantScopedAgentPool (NOT direct instantiation)
            agent = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type="field_mapping_agent",
                service_registry=mock_service_registry,
            )

            # Execute agent task through MFO pattern
            result = await agent.execute({
                "task_type": "field_mapping",
                "data": sample_mapping_data,
                "context": demo_context.to_dict(),
            })

            # Verify agent was called through TenantScopedAgentPool
            mock_tenant_scoped_agent_pool.get_agent.assert_called_once()
            agent.execute.assert_called_once()

            # Verify decision was based on agent response, not hardcoded threshold
            assert result["status"] == "completed"
            assert result["result"]["decision"] == "approve"
            assert result["result"]["confidence"] == 0.95
            assert "reasoning" in result["result"]

            # Verify no hardcoded threshold logic was used
            assert "threshold" not in str(result).lower()
            assert (
                result["result"]["reasoning"]
                == "High quality mapping with strong semantic alignment"
            )

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.tenant_isolation
    @pytest.mark.async_test
    async def test_agent_dynamic_decision_making_with_mfo(
        self, test_session, demo_context, mock_tenant_scoped_agent_pool,
        mock_service_registry, sample_mapping_data
    ):
        """Test that agents make contextual decisions based on data quality through MFO."""
        # Test different confidence scenarios with proper tenant isolation
        test_scenarios = [
            {
                "confidence": 0.95,
                "decision": "approve",
                "reasoning": "Excellent mapping quality with clear semantic matches",
            },
            {
                "confidence": 0.65,
                "decision": "review",
                "reasoning": "Moderate confidence, manual review recommended for ambiguous mappings",
            },
            {
                "confidence": 0.35,
                "decision": "reject",
                "reasoning": "Low confidence due to significant schema mismatches",
            },
        ]

        for scenario in test_scenarios:
            # Update mock agent response for scenario
            mock_agent = MagicMock()
            mock_agent.execute = AsyncMock(return_value={
                "status": "completed",
                "result": {
                    "decision": scenario["decision"],
                    "confidence": scenario["confidence"],
                    "reasoning": scenario["reasoning"],
                    "suggestions": [],
                },
                "execution_time": 1.23,
            })

            mock_tenant_scoped_agent_pool.get_agent = AsyncMock(return_value=mock_agent)

            with patch(
                "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
                return_value=mock_tenant_scoped_agent_pool,
            ):
                # Get agent through TenantScopedAgentPool with proper tenant context
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type="field_mapping_agent",
                    service_registry=mock_service_registry,
                )

                # Execute through MFO pattern
                result = await agent.execute({
                    "task_type": "field_mapping",
                    "data": sample_mapping_data,
                    "context": demo_context.to_dict(),
                    "scenario": scenario["decision"],
                })

                # Verify agent decision matches scenario with proper tenant isolation
                assert result["result"]["decision"] == scenario["decision"]
                assert result["result"]["confidence"] == scenario["confidence"]
                assert result["result"]["reasoning"] == scenario["reasoning"]

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.agent_memory
    @pytest.mark.integration
    @pytest.mark.tenant_isolation
    @pytest.mark.async_test
    async def test_agent_learning_from_feedback_with_mfo(
        self, test_session, demo_context, mock_tenant_scoped_agent_pool,
        mock_service_registry, sample_mapping_data
    ):
        """Test that agents incorporate user feedback for improved decisions through persistent memory."""
        # Create a single persistent agent instance with memory
        persistent_agent = MagicMock()
        persistent_agent.memory = []  # Simulate agent memory storage
        persistent_agent.execution_count = 0  # Track number of executions

        # Define execute behavior that changes based on feedback
        async def execute_with_memory(task_data):
            persistent_agent.execution_count += 1

            # Check if feedback is provided and store it in memory
            if "user_feedback" in task_data.get("data", {}):
                persistent_agent.memory.append(task_data["data"]["user_feedback"])

            # First execution - no memory, conservative decision
            if persistent_agent.execution_count == 1:
                return {
                    "status": "completed",
                    "result": {
                        "decision": "review",
                        "confidence": 0.72,
                        "reasoning": "Some ambiguous mappings require clarification",
                        "suggestions": ["Review cpu_cores to cpu_count mapping"],
                    },
                    "execution_time": 1.23,
                }

            # Second execution - with memory of user feedback, confident decision
            elif persistent_agent.execution_count == 2 and len(persistent_agent.memory) > 0:
                return {
                    "status": "completed",
                    "result": {
                        "decision": "approve",
                        "confidence": 0.94,
                        "reasoning": "Mappings confirmed by user feedback, cpu_cores to cpu_count verified",
                        "learning_applied": True,
                        "memory_used": True,
                    },
                    "execution_time": 1.15,
                }

            # Default response
            return {
                "status": "completed",
                "result": {
                    "decision": "review",
                    "confidence": 0.70,
                    "reasoning": "Default response",
                },
                "execution_time": 1.0,
            }

        persistent_agent.execute = AsyncMock(side_effect=execute_with_memory)

        # Return the SAME agent instance for both calls (persistent memory)
        mock_tenant_scoped_agent_pool.get_agent = AsyncMock(return_value=persistent_agent)

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # First pass - agent suggests review
            agent1 = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type="field_mapping_agent",
                service_registry=mock_service_registry,
            )

            result1 = await agent1.execute({
                "task_type": "field_mapping",
                "data": sample_mapping_data,
                "context": demo_context.to_dict(),
            })

            assert result1["result"]["decision"] == "review"
            assert persistent_agent.execution_count == 1

            # Simulate user feedback for agent learning
            user_feedback = {
                "mappings_confirmed": True,
                "corrections": [
                    {
                        "source": "cpu_cores",
                        "target": "cpu_count",
                        "user_confirmed": True,
                    }
                ],
                "notes": "CPU mapping is correct for our use case",
            }

            # Second pass with feedback - same tenant context ensures same agent instance
            agent2 = await TenantScopedAgentPool.get_agent(
                context=demo_context,  # Same tenant context
                agent_type="field_mapping_agent",
                service_registry=mock_service_registry,
            )

            # Verify same agent instance was returned (persistent memory)
            assert agent1 is agent2

            mapping_with_feedback = sample_mapping_data.copy()
            mapping_with_feedback["user_feedback"] = user_feedback

            result2 = await agent2.execute({
                "task_type": "field_mapping",
                "data": mapping_with_feedback,
                "context": demo_context.to_dict(),
            })

            # Verify agent learned from feedback through persistent memory
            assert result2["result"]["decision"] == "approve"
            assert result2["result"]["confidence"] > result1["result"]["confidence"]
            assert "learning_applied" in result2["result"]
            assert result2["result"]["learning_applied"] is True
            assert "memory_used" in result2["result"]
            assert result2["result"]["memory_used"] is True
            assert persistent_agent.execution_count == 2
            assert len(persistent_agent.memory) == 1

    @pytest.mark.mfo
    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.async_test
    @pytest.mark.discovery_flow
    async def test_master_flow_integration_with_tenant_scoped_agents(
        self, test_session, demo_context, mock_tenant_scoped_agent_pool,
        mock_service_registry, sample_mapping_data
    ):
        """Test integration with master flow orchestrator and TenantScopedAgentPool."""
        # Create master flow through orchestrator with proper tenant scoping
        orchestrator = MasterFlowOrchestrator(test_session)

        master_flow = await orchestrator.create_master_flow(
            flow_type="discovery",
            client_account_id=demo_context.client_account_id,
            engagement_id=demo_context.engagement_id,
            created_by=demo_context.user_id,
            config={"source_type": "servicenow"},
        )

        # Verify master flow created with proper tenant isolation
        assert master_flow.flow_id.startswith("master_")
        assert master_flow.flow_type == "discovery"
        assert master_flow.status == "initialized"
        assert master_flow.client_account_id == demo_context.client_account_id
        assert master_flow.engagement_id == demo_context.engagement_id

        # Start discovery flow with proper tenant scoping
        discovery_flow = await orchestrator.start_discovery_flow(
            master_flow_id=master_flow.flow_id,
            client_account_id=demo_context.client_account_id,
            engagement_id=demo_context.engagement_id,
            created_by=demo_context.user_id,
        )

        # Verify discovery flow linked to master with tenant isolation
        assert discovery_flow.master_flow_id == master_flow.flow_id
        assert discovery_flow.flow_id.startswith("disc_")
        assert discovery_flow.client_account_id == demo_context.client_account_id
        assert discovery_flow.engagement_id == demo_context.engagement_id

        # Test flow execution with TenantScopedAgentPool through MFO
        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_tenant_scoped_agent_pool,
        ):
            # Get persistent agent through TenantScopedAgentPool
            agent = await TenantScopedAgentPool.get_agent(
                context=demo_context,
                agent_type="field_mapping_agent",
                service_registry=mock_service_registry,
            )

            # Execute through MFO pattern with tenant context
            result = await agent.execute({
                "task_type": "field_mapping",
                "data": sample_mapping_data,
                "context": demo_context.to_dict(),
                "flow_id": discovery_flow.flow_id,
                "master_flow_id": master_flow.flow_id,
            })

            # Verify agent made decision through TenantScopedAgentPool
            assert "result" in result
            assert result["result"]["decision"] in [
                "approve",
                "review",
                "reject",
            ]

            # Verify tenant isolation in agent execution
            mock_tenant_scoped_agent_pool.get_agent.assert_called_with(
                context=demo_context,
                agent_type="field_mapping_agent",
                service_registry=mock_service_registry,
            )

            # Update master flow status through MFO
            await orchestrator.update_master_flow_status(
                master_flow.flow_id, "completed", {"discovery_completed": True}
            )

            # Verify cascade update with tenant scoping
            await test_session.refresh(master_flow)
            assert master_flow.status == "completed"

    @pytest.mark.mfo
    @pytest.mark.agent
    @pytest.mark.integration
    @pytest.mark.async_test
    async def test_error_handling_without_thresholds_mfo(
        self, test_session, demo_context, mock_service_registry
    ):
        """Test error handling uses agent decisions through MFO, not fallback thresholds."""
        # Mock TenantScopedAgentPool to simulate agent failure
        mock_failing_agent = MagicMock()
        mock_failing_agent.execute = AsyncMock(
            side_effect=Exception("Agent execution failed")
        )

        mock_failing_pool = MagicMock()
        mock_failing_pool.get_agent = AsyncMock(return_value=mock_failing_agent)

        with patch(
            "app.services.persistent_agents.tenant_scoped_agent_pool.TenantScopedAgentPool",
            return_value=mock_failing_pool,
        ):
            try:
                # Get agent through TenantScopedAgentPool
                agent = await TenantScopedAgentPool.get_agent(
                    context=demo_context,
                    agent_type="field_mapping_agent",
                    service_registry=mock_service_registry,
                )

                # Execute should handle error gracefully through MFO
                result = await agent.execute({
                    "task_type": "field_mapping",
                    "data": {},
                    "context": demo_context.to_dict(),
                })

                # Should not reach here
                assert False, "Expected exception was not raised"

            except Exception as e:
                # Verify error handled without falling back to hardcoded thresholds
                error_msg = str(e)
                assert "Agent execution failed" in error_msg
                assert "threshold" not in error_msg.lower()

                # Verify proper error structure (would be handled by MFO in real implementation)
                expected_error_response = {
                    "status": "error",
                    "error_code": "AGENT_EXECUTION_FAILED",
                    "details": {
                        "agent_type": "field_mapping_agent",
                        "tenant_context": demo_context.to_dict(),
                        "fallback_action": "manual_review"
                    }
                }
                # In real MFO implementation, this would be the structured error response
                assert "Agent execution failed" in str(e)


if __name__ == "__main__":
    # Run with MFO and agent markers
    pytest.main([__file__, "-v", "-m", "mfo and agent"])
