"""
Integration Tests for DecommissionAgentPool

Tests full crew execution flows and agent interactions.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.agents.decommission import DecommissionAgentPool


@pytest.mark.integration
class TestDecommissionAgentPoolIntegration:
    """Integration tests for complete decommission workflows"""

    @pytest.fixture
    def agent_pool(self):
        """Create agent pool for testing"""
        return DecommissionAgentPool()

    @pytest.fixture
    def mock_crewai_available(self):
        """Mock CrewAI availability"""
        with patch(
            "app.services.agents.decommission.agent_pool.CREWAI_AVAILABLE", True
        ):
            yield

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with API key"""
        with patch("app.services.agents.decommission.agent_pool.settings") as mock:
            mock.DEEPINFRA_API_KEY = "test-key"
            yield mock

    @pytest.mark.asyncio
    async def test_complete_planning_crew_workflow(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test complete planning crew workflow from agent creation to execution"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.Agent"
        ) as mock_agent_class:
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                with patch(
                    "app.services.agents.decommission.agent_pool.Crew"
                ) as mock_crew_class:
                    with patch("app.services.agents.decommission.agent_pool.Task"):
                        # Setup mocks
                        mock_agent_class.return_value = Mock()
                        mock_crew = Mock()
                        mock_crew.kickoff.return_value = {
                            "system_inventory": [],
                            "dependency_graph": {},
                            "retention_policies": {},
                        }
                        mock_crew_class.return_value = mock_crew

                        # Create agents
                        agents = {}
                        for key in [
                            "system_analysis_agent",
                            "dependency_mapper_agent",
                            "data_retention_agent",
                        ]:
                            agents[key] = await agent_pool.get_agent(
                                key, client_id, engagement_id
                            )

                        # Create crew
                        crew = agent_pool.create_decommission_planning_crew(
                            agents=agents,
                            system_ids=["sys1", "sys2"],
                            decommission_strategy={"priority": "cost_savings"},
                        )

                        # Execute
                        result = crew.kickoff()

                        # Verify
                        assert result is not None
                        assert "system_inventory" in result
                        assert mock_crew.kickoff.called

    @pytest.mark.asyncio
    async def test_complete_data_migration_crew_workflow(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test complete data migration crew workflow"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch("app.services.agents.decommission.agent_pool.Agent"):
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                with patch(
                    "app.services.agents.decommission.agent_pool.Crew"
                ) as mock_crew_class:
                    with patch("app.services.agents.decommission.agent_pool.Task"):
                        # Setup mocks
                        mock_crew = Mock()
                        mock_crew.kickoff.return_value = {
                            "archive_jobs": [],
                            "compliance_status": {},
                            "integrity_checks": {},
                        }
                        mock_crew_class.return_value = mock_crew

                        # Create agents
                        agents = {}
                        for key in [
                            "data_retention_agent",
                            "compliance_agent",
                            "validation_agent",
                        ]:
                            agents[key] = await agent_pool.get_agent(
                                key, client_id, engagement_id
                            )

                        # Create crew
                        crew = agent_pool.create_data_migration_crew(
                            agents=agents,
                            retention_policies={"policy1": {}},
                            system_ids=["sys1"],
                        )

                        # Execute
                        result = crew.kickoff()

                        # Verify
                        assert result is not None
                        assert "archive_jobs" in result
                        assert mock_crew.kickoff.called

    @pytest.mark.asyncio
    async def test_complete_shutdown_crew_workflow(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test complete system shutdown crew workflow"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch("app.services.agents.decommission.agent_pool.Agent"):
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                with patch(
                    "app.services.agents.decommission.agent_pool.Crew"
                ) as mock_crew_class:
                    with patch("app.services.agents.decommission.agent_pool.Task"):
                        # Setup mocks
                        mock_crew = Mock()
                        mock_crew.kickoff.return_value = {
                            "shutdown_results": {},
                            "validation_results": {"status": "passed"},
                            "rollback_procedures": {},
                        }
                        mock_crew_class.return_value = mock_crew

                        # Create agents
                        agents = {}
                        for key in [
                            "shutdown_orchestrator_agent",
                            "validation_agent",
                            "rollback_agent",
                        ]:
                            agents[key] = await agent_pool.get_agent(
                                key, client_id, engagement_id
                            )

                        # Create crew
                        crew = agent_pool.create_system_shutdown_crew(
                            agents=agents,
                            decommission_plan={"systems": [], "rollback_enabled": True},
                            system_ids=["sys1"],
                        )

                        # Execute
                        result = crew.kickoff()

                        # Verify
                        assert result is not None
                        assert "shutdown_results" in result
                        assert "validation_results" in result
                        assert mock_crew.kickoff.called

    @pytest.mark.asyncio
    async def test_agent_cache_across_crews(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test that agents are cached and reused across multiple crew creations"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.Agent"
        ) as mock_agent_class:
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                mock_agent_class.return_value = Mock()

                # Create validation_agent twice (used in both migration and shutdown crews)
                agent1 = await agent_pool.get_agent(
                    "validation_agent", client_id, engagement_id
                )
                agent2 = await agent_pool.get_agent(
                    "validation_agent", client_id, engagement_id
                )

                # Should be same instance (cached)
                assert agent1 == agent2
                # Should only create agent once
                assert mock_agent_class.call_count == 1

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test that agents are properly isolated per tenant"""
        client1 = str(uuid4())
        client2 = str(uuid4())
        engagement = str(uuid4())

        with patch(
            "app.services.agents.decommission.agent_pool.Agent"
        ) as mock_agent_class:
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                mock_agent1 = Mock()
                mock_agent2 = Mock()
                mock_agent_class.side_effect = [mock_agent1, mock_agent2]

                # Create same agent for two different tenants
                agent1 = await agent_pool.get_agent(
                    "system_analysis_agent", client1, engagement
                )
                agent2 = await agent_pool.get_agent(
                    "system_analysis_agent", client2, engagement
                )

                # Should be different instances (different tenants)
                assert agent1 != agent2
                assert agent1 == mock_agent1
                assert agent2 == mock_agent2
                # Should create agent twice (once per tenant)
                assert mock_agent_class.call_count == 2

    @pytest.mark.asyncio
    async def test_agent_release_cleans_cache(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test that release_agents properly cleans up tenant cache"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch("app.services.agents.decommission.agent_pool.Agent"):
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                # Create agents
                await agent_pool.get_agent(
                    "system_analysis_agent", client_id, engagement_id
                )
                await agent_pool.get_agent("validation_agent", client_id, engagement_id)

                # Verify cache has 2 entries
                assert len(agent_pool._agent_cache) == 2

                # Release agents
                await agent_pool.release_agents(client_id, engagement_id)

                # Cache should be empty for this tenant
                assert len(agent_pool._agent_cache) == 0

    @pytest.mark.asyncio
    async def test_memory_disabled_in_crew_creation(
        self, agent_pool, mock_crewai_available, mock_settings
    ):
        """Test that all crews are created with memory=False per ADR-024"""
        client_id = str(uuid4())
        engagement_id = str(uuid4())

        with patch("app.services.agents.decommission.agent_pool.Agent"):
            with patch("app.services.agents.decommission.agent_pool.LLM"):
                with patch(
                    "app.services.agents.decommission.agent_pool.Crew"
                ) as mock_crew_class:
                    with patch("app.services.agents.decommission.agent_pool.Task"):
                        # Create agents for all crews
                        all_agents = {}
                        for key in agent_pool.get_available_agents():
                            all_agents[key] = await agent_pool.get_agent(
                                key, client_id, engagement_id
                            )

                        # Test planning crew
                        agent_pool.create_decommission_planning_crew(
                            agents={
                                k: v
                                for k, v in all_agents.items()
                                if k
                                in [
                                    "system_analysis_agent",
                                    "dependency_mapper_agent",
                                    "data_retention_agent",
                                ]
                            },
                            system_ids=[],
                            decommission_strategy={},
                        )

                        # Verify memory=False
                        call_kwargs = mock_crew_class.call_args[1]
                        assert call_kwargs.get("memory") is False

                        mock_crew_class.reset_mock()

                        # Test data migration crew
                        agent_pool.create_data_migration_crew(
                            agents={
                                k: v
                                for k, v in all_agents.items()
                                if k
                                in [
                                    "data_retention_agent",
                                    "compliance_agent",
                                    "validation_agent",
                                ]
                            },
                            retention_policies={},
                            system_ids=[],
                        )

                        # Verify memory=False
                        call_kwargs = mock_crew_class.call_args[1]
                        assert call_kwargs.get("memory") is False

                        mock_crew_class.reset_mock()

                        # Test shutdown crew
                        agent_pool.create_system_shutdown_crew(
                            agents={
                                k: v
                                for k, v in all_agents.items()
                                if k
                                in [
                                    "shutdown_orchestrator_agent",
                                    "validation_agent",
                                    "rollback_agent",
                                ]
                            },
                            decommission_plan={},
                            system_ids=[],
                        )

                        # Verify memory=False
                        call_kwargs = mock_crew_class.call_args[1]
                        assert call_kwargs.get("memory") is False
