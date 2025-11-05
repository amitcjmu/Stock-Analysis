"""
Unit Tests for DecommissionAgentPool

Tests agent initialization, crew creation, and configuration.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.agents.decommission import (
    DecommissionAgentPool,
    DECOMMISSION_AGENT_CONFIGS,
)


class TestDecommissionAgentPool:
    """Test suite for DecommissionAgentPool"""

    @pytest.fixture
    def agent_pool(self):
        """Create agent pool instance for testing"""
        return DecommissionAgentPool()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with DeepInfra API key"""
        with patch("app.services.agents.decommission.agent_pool.settings") as mock:
            mock.DEEPINFRA_API_KEY = "test-api-key"
            yield mock

    def test_initialization(self, agent_pool):
        """Test agent pool initialization"""
        assert agent_pool is not None
        assert agent_pool.agent_configs == DECOMMISSION_AGENT_CONFIGS
        assert isinstance(agent_pool._agent_cache, dict)
        assert len(agent_pool._agent_cache) == 0

    def test_agent_configurations(self, agent_pool):
        """Test that all 7 agent configurations are defined"""
        expected_agents = [
            "system_analysis_agent",
            "dependency_mapper_agent",
            "data_retention_agent",
            "compliance_agent",
            "shutdown_orchestrator_agent",
            "validation_agent",
            "rollback_agent",
        ]

        for agent_key in expected_agents:
            assert agent_key in agent_pool.agent_configs
            config = agent_pool.agent_configs[agent_key]
            assert "role" in config
            assert "goal" in config
            assert "backstory" in config
            assert "llm_config" in config
            assert config["memory_enabled"] is False  # Per ADR-024

    def test_memory_disabled_for_all_agents(self, agent_pool):
        """Test that memory is disabled for all agents per ADR-024"""
        for agent_key, config in agent_pool.agent_configs.items():
            assert config.get("memory_enabled") is False, (
                f"Agent {agent_key} has memory_enabled={config.get('memory_enabled')}, "
                "but ADR-024 requires memory=False"
            )

    @pytest.mark.asyncio
    async def test_get_agent_creates_new_agent(self, agent_pool, mock_settings):
        """Test that get_agent creates a new agent instance"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch(
                "app.services.agents.decommission.agent_pool.Agent"
            ) as mock_agent_class:
                with patch(
                    "app.services.agents.decommission.agent_pool.LLM"
                ) as mock_llm_class:
                    mock_llm = Mock()
                    mock_llm_class.return_value = mock_llm

                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent

                    agent = await agent_pool.get_agent(
                        "system_analysis_agent", client_id, engagement_id
                    )

                    assert agent == mock_agent
                    mock_agent_class.assert_called_once()
                    mock_llm_class.assert_called_once()

                    # Verify agent metadata
                    assert agent._client_account_id == client_id
                    assert agent._engagement_id == engagement_id
                    assert agent._agent_key == "system_analysis_agent"

    @pytest.mark.asyncio
    async def test_get_agent_uses_cache(self, agent_pool, mock_settings):
        """Test that get_agent returns cached agent on second call"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch(
                "app.services.agents.decommission.agent_pool.Agent"
            ) as mock_agent_class:
                with patch("app.services.agents.decommission.agent_pool.LLM"):
                    mock_agent = Mock()
                    mock_agent_class.return_value = mock_agent

                    # First call - creates agent
                    agent1 = await agent_pool.get_agent(
                        "system_analysis_agent", client_id, engagement_id
                    )

                    # Second call - uses cache
                    agent2 = await agent_pool.get_agent(
                        "system_analysis_agent", client_id, engagement_id
                    )

                    assert agent1 == agent2
                    # Should only create agent once
                    assert mock_agent_class.call_count == 1

    @pytest.mark.asyncio
    async def test_get_agent_invalid_key(self, agent_pool):
        """Test that get_agent raises error for invalid agent key"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with pytest.raises(ValueError, match="Unknown agent key"):
            await agent_pool.get_agent("invalid_agent", client_id, engagement_id)

    def test_get_available_agents(self, agent_pool):
        """Test get_available_agents returns all 7 agents"""
        agents = agent_pool.get_available_agents()
        assert len(agents) == 7
        assert "system_analysis_agent" in agents
        assert "dependency_mapper_agent" in agents
        assert "data_retention_agent" in agents
        assert "compliance_agent" in agents
        assert "shutdown_orchestrator_agent" in agents
        assert "validation_agent" in agents
        assert "rollback_agent" in agents

    def test_get_agent_info(self, agent_pool):
        """Test get_agent_info returns correct configuration"""
        info = agent_pool.get_agent_info("system_analysis_agent")

        assert info["agent_key"] == "system_analysis_agent"
        assert "role" in info
        assert "goal" in info
        assert "tools" in info
        assert info["memory_enabled"] is False
        assert "llm_model" in info

    def test_get_agent_info_invalid_key(self, agent_pool):
        """Test get_agent_info raises error for invalid key"""
        with pytest.raises(ValueError, match="Unknown agent key"):
            agent_pool.get_agent_info("invalid_agent")

    @pytest.mark.asyncio
    async def test_release_agents(self, agent_pool, mock_settings):
        """Test release_agents clears cache for specific tenant"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())
        other_client = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch("app.services.agents.decommission.agent_pool.Agent"):
                with patch("app.services.agents.decommission.agent_pool.LLM"):
                    # Create agents for two different tenants
                    await agent_pool.get_agent(
                        "system_analysis_agent", client_id, engagement_id
                    )
                    await agent_pool.get_agent(
                        "system_analysis_agent", other_client, engagement_id
                    )

                    assert len(agent_pool._agent_cache) == 2

                    # Release agents for one tenant
                    await agent_pool.release_agents(client_id, engagement_id)

                    # Only one tenant's agents should remain
                    assert len(agent_pool._agent_cache) == 1
                    assert (
                        f"{other_client}:{engagement_id}:system_analysis_agent"
                        in agent_pool._agent_cache
                    )

    def test_create_decommission_planning_crew(self, agent_pool):
        """Test decommission planning crew creation"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch(
                "app.services.agents.decommission.agent_pool.Crew"
            ) as mock_crew_class:
                with patch(
                    "app.services.agents.decommission.agent_pool.Task"
                ) as mock_task_class:
                    mock_agents = {
                        "system_analysis_agent": Mock(),
                        "dependency_mapper_agent": Mock(),
                        "data_retention_agent": Mock(),
                    }

                    mock_crew = Mock()
                    mock_crew_class.return_value = mock_crew

                    crew = agent_pool.create_decommission_planning_crew(
                        agents=mock_agents,
                        system_ids=["sys1", "sys2"],
                        decommission_strategy={"priority": "cost_savings"},
                    )

                    assert crew == mock_crew
                    # Should create 3 tasks (analysis, mapping, retention)
                    assert mock_task_class.call_count == 3
                    # Should create crew with memory=False
                    mock_crew_class.assert_called_once()
                    call_kwargs = mock_crew_class.call_args[1]
                    assert call_kwargs["memory"] is False  # Per ADR-024

    def test_create_decommission_planning_crew_missing_agents(self, agent_pool):
        """Test planning crew raises error if agents missing"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            mock_agents = {
                "system_analysis_agent": Mock(),
                # Missing dependency_mapper_agent and data_retention_agent
            }

            with pytest.raises(ValueError, match="Missing required agents"):
                agent_pool.create_decommission_planning_crew(
                    agents=mock_agents,
                    system_ids=["sys1"],
                    decommission_strategy={},
                )

    def test_create_data_migration_crew(self, agent_pool):
        """Test data migration crew creation"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch(
                "app.services.agents.decommission.agent_pool.Crew"
            ) as mock_crew_class:
                with patch(
                    "app.services.agents.decommission.agent_pool.Task"
                ) as mock_task_class:
                    mock_agents = {
                        "data_retention_agent": Mock(),
                        "compliance_agent": Mock(),
                        "validation_agent": Mock(),
                    }

                    mock_crew = Mock()
                    mock_crew_class.return_value = mock_crew

                    crew = agent_pool.create_data_migration_crew(
                        agents=mock_agents,
                        retention_policies={"policy1": {}},
                        system_ids=["sys1"],
                    )

                    assert crew == mock_crew
                    # Should create 3 tasks (archive, compliance, validation)
                    assert mock_task_class.call_count == 3
                    # Should create crew with memory=False
                    call_kwargs = mock_crew_class.call_args[1]
                    assert call_kwargs["memory"] is False  # Per ADR-024

    def test_create_system_shutdown_crew(self, agent_pool):
        """Test system shutdown crew creation"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            with patch(
                "app.services.agents.decommission.agent_pool.Crew"
            ) as mock_crew_class:
                with patch(
                    "app.services.agents.decommission.agent_pool.Task"
                ) as mock_task_class:
                    mock_agents = {
                        "shutdown_orchestrator_agent": Mock(),
                        "validation_agent": Mock(),
                        "rollback_agent": Mock(),
                    }

                    mock_crew = Mock()
                    mock_crew_class.return_value = mock_crew

                    crew = agent_pool.create_system_shutdown_crew(
                        agents=mock_agents,
                        decommission_plan={"systems": [], "rollback_enabled": True},
                        system_ids=["sys1"],
                    )

                    assert crew == mock_crew
                    # Should create 3 tasks (shutdown, validation, rollback readiness)
                    assert mock_task_class.call_count == 3
                    # Should create crew with memory=False
                    call_kwargs = mock_crew_class.call_args[1]
                    assert call_kwargs["memory"] is False  # Per ADR-024

    def test_fallback_mode_when_crewai_unavailable(self, agent_pool):
        """Test agent pool works in fallback mode when CrewAI unavailable"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", False
        ):
            # Should not raise errors in fallback mode
            crew = agent_pool.create_decommission_planning_crew(
                agents={},
                system_ids=[],
                decommission_strategy={},
            )

            # Crew should be None in fallback mode
            assert crew is None


class TestDecommissionAgentConfigs:
    """Test agent configuration definitions"""

    def test_all_agents_have_llm_config(self):
        """Test that all agents have LLM configuration"""
        for agent_key, config in DECOMMISSION_AGENT_CONFIGS.items():
            assert "llm_config" in config, f"{agent_key} missing llm_config"
            assert "provider" in config["llm_config"]
            assert "model" in config["llm_config"]
            assert config["llm_config"]["provider"] == "deepinfra"

    def test_all_agents_use_llama_4(self):
        """Test that all agents use Llama 4 model"""
        for agent_key, config in DECOMMISSION_AGENT_CONFIGS.items():
            model = config["llm_config"]["model"]
            assert "Llama-4" in model, f"{agent_key} not using Llama 4: {model}"

    def test_agent_roles_unique(self):
        """Test that all agents have unique roles"""
        roles = [config["role"] for config in DECOMMISSION_AGENT_CONFIGS.values()]
        assert len(roles) == len(set(roles)), "Duplicate agent roles found"

    def test_agent_goals_defined(self):
        """Test that all agents have meaningful goals"""
        for agent_key, config in DECOMMISSION_AGENT_CONFIGS.items():
            assert (
                len(config["goal"]) > 50
            ), f"{agent_key} goal too short: {len(config['goal'])} chars"

    def test_agent_backstories_detailed(self):
        """Test that all agents have detailed backstories"""
        for agent_key, config in DECOMMISSION_AGENT_CONFIGS.items():
            assert (
                len(config["backstory"]) > 100
            ), f"{agent_key} backstory too short: {len(config['backstory'])} chars"
