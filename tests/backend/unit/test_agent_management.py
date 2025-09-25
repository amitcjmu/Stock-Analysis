"""
Unit Tests for Agent Management Components - High Impact

This module provides comprehensive unit tests for agent management components
in the discovery flow, covering agent pools, crew coordination, and persistence.

Test Coverage:
- TenantScopedAgentPool
- UnifiedFlowCrewManager
- CrewCoordinator
- Agent Persistence
- Memory Management
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Any, Dict, List
import uuid

# Import agent management components
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from app.services.crewai_flows.handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
from app.services.crewai_flows.unified_discovery_flow.crew_coordination import CrewCoordinator


class MockAgent:
    """Mock agent for testing"""

    def __init__(self, agent_type: str, agent_id: str = None):
        self.agent_type = agent_type
        self.agent_id = agent_id or str(uuid.uuid4())
        self.memory = {}
        self.execution_count = 0
        self.last_execution = None

    async def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock agent execution"""
        self.execution_count += 1
        self.last_execution = datetime.now().isoformat()

        # Simulate different agent behaviors
        if self.agent_type == "data_validation":
            return {
                "status": "success",
                "validation_results": {"is_valid": True, "quality_score": 0.95},
                "agent_id": self.agent_id
            }
        elif self.agent_type == "field_mapping":
            return {
                "status": "success",
                "field_mappings": {"hostname": {"target": "server_name", "confidence": 0.95}},
                "agent_id": self.agent_id
            }
        elif self.agent_type == "data_cleansing":
            return {
                "status": "success",
                "cleaned_data": [{"id": 1, "hostname": "server-01"}],
                "quality_metrics": {"data_quality_score": 0.95},
                "agent_id": self.agent_id
            }
        else:
            return {
                "status": "success",
                "result": f"Processed by {self.agent_type} agent",
                "agent_id": self.agent_id
            }

    def add_memory(self, key: str, value: Any):
        """Add memory to agent"""
        self.memory[key] = value

    def get_memory(self, key: str) -> Any:
        """Get memory from agent"""
        return self.memory.get(key)


class MockContext:
    """Mock context for testing"""

    def __init__(self):
        self.client_account_id = str(uuid.uuid4())
        self.engagement_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())


class MockCrew:
    """Mock crew for testing"""

    def __init__(self, crew_type: str, agents: List[MockAgent] = None):
        self.crew_type = crew_type
        self.agents = agents or []
        self.execution_count = 0
        self.last_execution = None

    async def kickoff(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock crew execution"""
        self.execution_count += 1
        self.last_execution = datetime.now().isoformat()

        # Simulate crew execution by combining agent results
        results = {
            "status": "success",
            "crew_type": self.crew_type,
            "execution_count": self.execution_count,
            "agent_results": []
        }

        for agent in self.agents:
            agent_result = await agent.execute(inputs or {})
            results["agent_results"].append(agent_result)

        return results


@pytest.fixture
def mock_context():
    """Create mock context"""
    return MockContext()


@pytest.fixture
def sample_agents():
    """Create sample agents for testing"""
    return [
        MockAgent("data_validation"),
        MockAgent("field_mapping"),
        MockAgent("data_cleansing"),
        MockAgent("asset_inventory"),
        MockAgent("dependency_analysis"),
        MockAgent("tech_debt_analysis")
    ]


@pytest.fixture
def sample_crews(sample_agents):
    """Create sample crews for testing"""
    return {
        "data_validation": MockCrew("data_validation", [sample_agents[0]]),
        "field_mapping": MockCrew("field_mapping", [sample_agents[1]]),
        "data_cleansing": MockCrew("data_cleansing", [sample_agents[2]]),
        "asset_inventory": MockCrew("asset_inventory", [sample_agents[3]]),
        "dependency_analysis": MockCrew("dependency_analysis", [sample_agents[4]]),
        "tech_debt_analysis": MockCrew("tech_debt_analysis", [sample_agents[5]])
    }


class TestTenantScopedAgentPool:
    """Test TenantScopedAgentPool functionality"""

    @pytest.fixture
    def agent_pool(self, mock_context):
        """Create agent pool instance"""
        return TenantScopedAgentPool(mock_context)

    def test_initialization(self, agent_pool, mock_context):
        """Test agent pool initialization"""
        assert agent_pool.context == mock_context
        assert agent_pool.client_account_id == mock_context.client_account_id
        assert agent_pool.engagement_id == mock_context.engagement_id
        assert agent_pool.user_id == mock_context.user_id
        assert agent_pool._agent_cache == {}
        assert agent_pool._agent_creation_count == {}

    @pytest.mark.asyncio
    async def test_get_agent_new_creation(self, agent_pool):
        """Test getting a new agent"""
        agent_type = "data_validation"

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent(agent_type)
            mock_create.return_value = mock_agent

            agent = await agent_pool.get_agent(agent_type)

            assert agent == mock_agent
            assert agent_type in agent_pool._agent_cache
            assert agent_pool._agent_cache[agent_type] == mock_agent
            assert agent_pool._agent_creation_count[agent_type] == 1
            mock_create.assert_called_once_with(agent_type)

    @pytest.mark.asyncio
    async def test_get_agent_cached(self, agent_pool):
        """Test getting a cached agent"""
        agent_type = "field_mapping"
        mock_agent = MockAgent(agent_type)

        # Pre-populate cache
        agent_pool._agent_cache[agent_type] = mock_agent
        agent_pool._agent_creation_count[agent_type] = 1

        with patch.object(agent_pool, '_create_agent') as mock_create:
            agent = await agent_pool.get_agent(agent_type)

            assert agent == mock_agent
            assert agent_pool._agent_creation_count[agent_type] == 1  # Should not increment
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_agent_with_context(self, agent_pool, mock_context):
        """Test getting agent with context"""
        agent_type = "data_cleansing"

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent(agent_type)
            mock_create.return_value = mock_agent

            agent = await agent_pool.get_agent(agent_type, context=mock_context)

            assert agent == mock_agent
            mock_create.assert_called_once_with(agent_type, context=mock_context)

    @pytest.mark.asyncio
    async def test_execute_with_agent(self, agent_pool):
        """Test executing task with agent"""
        agent_type = "data_validation"
        task_data = {"raw_data": [{"hostname": "server-01"}]}

        with patch.object(agent_pool, 'get_agent') as mock_get_agent:
            mock_agent = MockAgent(agent_type)
            mock_get_agent.return_value = mock_agent

            result = await agent_pool.execute_with_agent(agent_type, task_data)

            assert result["status"] == "success"
            assert "validation_results" in result
            assert result["agent_id"] == mock_agent.agent_id
            mock_get_agent.assert_called_once_with(agent_type)

    @pytest.mark.asyncio
    async def test_agent_persistence_across_calls(self, agent_pool):
        """Test agent persistence across multiple calls"""
        agent_type = "field_mapping"

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent(agent_type)
            mock_create.return_value = mock_agent

            # First call
            agent1 = await agent_pool.get_agent(agent_type)

            # Second call
            agent2 = await agent_pool.get_agent(agent_type)

            # Should be the same agent instance
            assert agent1 == agent2
            assert agent1 is agent2
            assert mock_create.call_count == 1  # Only created once

    @pytest.mark.asyncio
    async def test_agent_memory_persistence(self, agent_pool):
        """Test agent memory persistence across calls"""
        agent_type = "data_cleansing"

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent(agent_type)
            mock_create.return_value = mock_agent

            # First call - add memory
            agent1 = await agent_pool.get_agent(agent_type)
            agent1.add_memory("previous_task", "processed_100_records")

            # Second call - retrieve memory
            agent2 = await agent_pool.get_agent(agent_type)
            memory_value = agent2.get_memory("previous_task")

            assert memory_value == "processed_100_records"
            assert agent1 is agent2  # Same instance

    @pytest.mark.asyncio
    async def test_multiple_agent_types(self, agent_pool):
        """Test managing multiple agent types"""
        agent_types = ["data_validation", "field_mapping", "data_cleansing"]

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_create.side_effect = lambda agent_type: MockAgent(agent_type)

            # Get different agent types
            agents = {}
            for agent_type in agent_types:
                agents[agent_type] = await agent_pool.get_agent(agent_type)

            # Verify all agents are different instances
            assert len(set(id(agent) for agent in agents.values())) == len(agent_types)

            # Verify all agents are cached
            for agent_type in agent_types:
                assert agent_type in agent_pool._agent_cache
                assert agent_pool._agent_creation_count[agent_type] == 1

    @pytest.mark.asyncio
    async def test_agent_execution_tracking(self, agent_pool):
        """Test agent execution tracking"""
        agent_type = "asset_inventory"

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent(agent_type)
            mock_create.return_value = mock_agent

            # Execute multiple tasks
            task_data1 = {"assets": [{"id": 1, "name": "server-01"}]}
            task_data2 = {"assets": [{"id": 2, "name": "server-02"}]}

            await agent_pool.execute_with_agent(agent_type, task_data1)
            await agent_pool.execute_with_agent(agent_type, task_data2)

            # Verify execution tracking
            assert mock_agent.execution_count == 2
            assert mock_agent.last_execution is not None


class TestUnifiedFlowCrewManager:
    """Test UnifiedFlowCrewManager functionality"""

    @pytest.fixture
    def crew_manager(self, mock_context, sample_agents):
        """Create crew manager instance"""
        return UnifiedFlowCrewManager(
            crewai_service=Mock(),
            state=Mock(),
            callback_handler=None,
            context=mock_context
        )

    def test_initialization(self, crew_manager, mock_context):
        """Test crew manager initialization"""
        assert crew_manager.context == mock_context
        assert crew_manager.client_account_id == mock_context.client_account_id
        assert crew_manager.engagement_id == mock_context.engagement_id
        assert crew_manager.user_id == mock_context.user_id

    @pytest.mark.asyncio
    async def test_create_crew_on_demand(self, crew_manager, sample_agents):
        """Test creating crew on demand"""
        crew_type = "data_validation"

        with patch.object(crew_manager, '_create_crew') as mock_create_crew:
            mock_crew = MockCrew(crew_type, [sample_agents[0]])
            mock_create_crew.return_value = mock_crew

            crew = crew_manager.create_crew_on_demand(crew_type)

            assert crew == mock_crew
            mock_create_crew.assert_called_once_with(crew_type)

    @pytest.mark.asyncio
    async def test_execute_crew(self, crew_manager, sample_agents):
        """Test executing crew"""
        crew_type = "field_mapping"
        inputs = {"field_mappings": {"hostname": "server_name"}}

        with patch.object(crew_manager, 'create_crew_on_demand') as mock_create:
            mock_crew = MockCrew(crew_type, [sample_agents[1]])
            mock_create.return_value = mock_crew

            result = await crew_manager.execute_crew(crew_type, inputs)

            assert result["status"] == "success"
            assert result["crew_type"] == crew_type
            assert "agent_results" in result
            mock_create.assert_called_once_with(crew_type)

    @pytest.mark.asyncio
    async def test_coordinate_multiple_crews(self, crew_manager, sample_agents):
        """Test coordinating multiple crews"""
        crew_types = ["data_validation", "field_mapping", "data_cleansing"]

        with patch.object(crew_manager, 'create_crew_on_demand') as mock_create:
            mock_create.side_effect = lambda crew_type: MockCrew(crew_type, [sample_agents[0]])

            results = {}
            for crew_type in crew_types:
                result = await crew_manager.execute_crew(crew_type, {})
                results[crew_type] = result

            # Verify all crews executed successfully
            assert len(results) == len(crew_types)
            for crew_type, result in results.items():
                assert result["status"] == "success"
                assert result["crew_type"] == crew_type

    @pytest.mark.asyncio
    async def test_crew_error_handling(self, crew_manager):
        """Test crew error handling"""
        crew_type = "data_validation"

        with patch.object(crew_manager, 'create_crew_on_demand') as mock_create:
            mock_crew = MockCrew(crew_type, [])
            mock_crew.kickoff = AsyncMock(side_effect=Exception("Crew execution failed"))
            mock_create.return_value = mock_crew

            with pytest.raises(Exception, match="Crew execution failed"):
                await crew_manager.execute_crew(crew_type, {})


class TestCrewCoordinator:
    """Test CrewCoordinator functionality"""

    @pytest.fixture
    def crew_coordinator(self, mock_context):
        """Create crew coordinator instance"""
        return CrewCoordinator(
            crewai_service=Mock(),
            context=mock_context,
            agent_timeout=300
        )

    def test_initialization(self, crew_coordinator, mock_context):
        """Test crew coordinator initialization"""
        assert crew_coordinator.context == mock_context
        assert crew_coordinator.client_account_id == mock_context.client_account_id
        assert crew_coordinator.engagement_id == mock_context.engagement_id
        assert crew_coordinator.user_id == mock_context.user_id
        assert crew_coordinator.agent_timeout == 300

    @pytest.mark.asyncio
    async def test_coordinate_phase_execution(self, crew_coordinator, sample_crews):
        """Test coordinating phase execution"""
        phase = "data_validation"
        phase_data = {"raw_data": [{"hostname": "server-01"}]}

        with patch.object(crew_coordinator, '_get_crew_for_phase') as mock_get_crew:
            mock_get_crew.return_value = sample_crews["data_validation"]

            result = await crew_coordinator.coordinate_phase_execution(phase, phase_data)

            assert result["status"] == "success"
            assert result["crew_type"] == "data_validation"
            mock_get_crew.assert_called_once_with(phase)

    @pytest.mark.asyncio
    async def test_coordinate_sequential_phases(self, crew_coordinator, sample_crews):
        """Test coordinating sequential phase execution"""
        phases = ["data_validation", "field_mapping", "data_cleansing"]
        phase_data = {"raw_data": [{"hostname": "server-01"}]}

        with patch.object(crew_coordinator, '_get_crew_for_phase') as mock_get_crew:
            mock_get_crew.side_effect = lambda phase: sample_crews.get(phase, MockCrew(phase))

            results = []
            for phase in phases:
                result = await crew_coordinator.coordinate_phase_execution(phase, phase_data)
                results.append(result)

            # Verify all phases executed successfully
            assert len(results) == len(phases)
            for i, result in enumerate(results):
                assert result["status"] == "success"
                assert result["crew_type"] == phases[i]

    @pytest.mark.asyncio
    async def test_coordinate_parallel_phases(self, crew_coordinator, sample_crews):
        """Test coordinating parallel phase execution"""
        phases = ["dependency_analysis", "tech_debt_analysis"]
        phase_data = {"assets": [{"id": 1, "name": "server-01"}]}

        with patch.object(crew_coordinator, '_get_crew_for_phase') as mock_get_crew:
            mock_get_crew.side_effect = lambda phase: sample_crews.get(phase, MockCrew(phase))

            # Execute phases in parallel
            tasks = [
                crew_coordinator.coordinate_phase_execution(phase, phase_data)
                for phase in phases
            ]

            results = await asyncio.gather(*tasks)

            # Verify all phases executed successfully
            assert len(results) == len(phases)
            for i, result in enumerate(results):
                assert result["status"] == "success"
                assert result["crew_type"] == phases[i]

    @pytest.mark.asyncio
    async def test_phase_dependency_handling(self, crew_coordinator, sample_crews):
        """Test handling phase dependencies"""
        phase = "data_cleansing"
        phase_data = {"raw_data": [{"hostname": "server-01"}]}
        previous_results = {
            "data_validation": {"status": "success", "validated_data": []},
            "field_mapping": {"status": "success", "field_mappings": {}}
        }

        with patch.object(crew_coordinator, '_get_crew_for_phase') as mock_get_crew:
            mock_get_crew.return_value = sample_crews["data_cleansing"]

            result = await crew_coordinator.coordinate_phase_execution(
                phase, phase_data, previous_results
            )

            assert result["status"] == "success"
            assert result["crew_type"] == "data_cleansing"
            mock_get_crew.assert_called_once_with(phase)


class TestAgentManagementIntegration:
    """Test integration between agent management components"""

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, mock_context, sample_agents):
        """Test complete agent workflow"""
        # Initialize agent pool
        agent_pool = TenantScopedAgentPool(mock_context)

        # Initialize crew manager
        crew_manager = UnifiedFlowCrewManager(
            crewai_service=Mock(),
            state=Mock(),
            callback_handler=None,
            context=mock_context
        )

        # Initialize crew coordinator
        crew_coordinator = CrewCoordinator(
            crewai_service=Mock(),
            context=mock_context,
            agent_timeout=300
        )

        # Test agent pool operations
        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_create.side_effect = lambda agent_type: MockAgent(agent_type)

            # Get agents for different phases
            validation_agent = await agent_pool.get_agent("data_validation")
            mapping_agent = await agent_pool.get_agent("field_mapping")

            # Verify agents are different instances
            assert validation_agent != mapping_agent
            assert validation_agent.agent_type == "data_validation"
            assert mapping_agent.agent_type == "field_mapping"

            # Test agent memory persistence
            validation_agent.add_memory("previous_task", "validated_100_records")
            retrieved_memory = validation_agent.get_memory("previous_task")
            assert retrieved_memory == "validated_100_records"

        # Test crew coordination
        with patch.object(crew_coordinator, '_get_crew_for_phase') as mock_get_crew:
            mock_get_crew.side_effect = lambda phase: MockCrew(phase, [MockAgent(phase)])

            # Execute sequential phases
            phases = ["data_validation", "field_mapping", "data_cleansing"]
            results = []

            for phase in phases:
                result = await crew_coordinator.coordinate_phase_execution(phase, {})
                results.append(result)

            # Verify all phases completed successfully
            assert len(results) == len(phases)
            for i, result in enumerate(results):
                assert result["status"] == "success"
                assert result["crew_type"] == phases[i]

    @pytest.mark.asyncio
    async def test_agent_persistence_across_workflow(self, mock_context):
        """Test agent persistence across complete workflow"""
        agent_pool = TenantScopedAgentPool(mock_context)

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_create.side_effect = lambda agent_type: MockAgent(agent_type)

            # Simulate workflow phases
            phases = ["data_validation", "field_mapping", "data_cleansing"]

            for phase in phases:
                # Get agent for phase
                agent = await agent_pool.get_agent(phase)

                # Execute task
                task_data = {"phase": phase, "data": [{"id": 1}]}
                result = await agent_pool.execute_with_agent(phase, task_data)

                # Add memory for next phase
                agent.add_memory(f"{phase}_completed", f"processed_{phase}")

                # Verify agent persistence
                assert result["status"] == "success"
                assert agent.execution_count > 0

            # Verify all agents are cached
            assert len(agent_pool._agent_cache) == len(phases)
            for phase in phases:
                assert phase in agent_pool._agent_cache
                assert agent_pool._agent_creation_count[phase] == 1

    @pytest.mark.asyncio
    async def test_error_recovery_in_agent_management(self, mock_context):
        """Test error recovery in agent management"""
        agent_pool = TenantScopedAgentPool(mock_context)

        with patch.object(agent_pool, '_create_agent') as mock_create:
            mock_agent = MockAgent("data_validation")
            mock_agent.execute = AsyncMock(side_effect=Exception("Agent execution failed"))
            mock_create.return_value = mock_agent

            # Test error handling
            with pytest.raises(Exception, match="Agent execution failed"):
                await agent_pool.execute_with_agent("data_validation", {})

            # Verify agent is still cached (for retry)
            assert "data_validation" in agent_pool._agent_cache
            assert agent_pool._agent_cache["data_validation"] == mock_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
