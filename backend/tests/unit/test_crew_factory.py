"""
Unit tests for CrewAI Factory Pattern

Tests verify that the factory pattern correctly applies defaults
and allows overrides without global monkey patches.
"""

import os
import pytest
from unittest.mock import Mock, patch

# Import factory components
from app.services.crewai_flows.config.crew_factory import (
    CrewConfig,
    CrewFactory,
    CrewMemoryManager,
    create_agent,
    create_crew,
    create_task,
)


class TestCrewConfig:
    """Test CrewConfig default configuration."""

    def test_default_agent_config(self):
        """Test default agent configuration."""
        config = CrewConfig.get_agent_defaults()

        assert config["allow_delegation"] is False
        assert config["max_delegation"] == 0
        assert config["max_iter"] == 1
        assert config["verbose"] is False

    def test_agent_config_overrides(self):
        """Test agent configuration with overrides."""
        config = CrewConfig.get_agent_defaults(
            allow_delegation=True,
            max_iter=3,
            verbose=True,
        )

        assert config["allow_delegation"] is True
        assert config["max_delegation"] == 1  # Set to 1 when delegation enabled
        assert config["max_iter"] == 3
        assert config["verbose"] is True

    def test_default_crew_config(self):
        """Test default crew configuration."""
        config = CrewConfig.get_crew_defaults()

        assert config["max_iterations"] == 1
        assert config["verbose"] is False
        assert config["memory"] is False  # Per ADR-024: Use TenantMemoryManager instead
        assert config["max_execution_time"] > 0  # From env or default

    def test_crew_config_overrides(self):
        """Test crew configuration with overrides."""
        config = CrewConfig.get_crew_defaults(
            max_execution_time=1200,
            max_iterations=3,
            verbose=True,
            memory=False,
        )

        assert config["max_execution_time"] == 1200
        assert config["max_iterations"] == 3
        assert config["verbose"] is True
        assert config["memory"] is False

    def test_get_default_timeout_from_env(self):
        """Test timeout reading from environment variable."""
        with patch.dict(os.environ, {"CREWAI_TIMEOUT_SECONDS": "900"}):
            timeout = CrewConfig.get_default_timeout()
            assert timeout == 900


class TestCrewFactory:
    """Test CrewFactory agent and crew creation."""

    def test_factory_initialization(self):
        """Test factory initialization with defaults."""
        factory = CrewFactory(enable_memory=True, verbose=False)

        assert factory.enable_memory is True
        assert factory.verbose is False
        assert factory.default_timeout > 0

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Agent")
    def test_create_agent_with_defaults(self, mock_agent_class):
        """Test agent creation with default configuration."""
        factory = CrewFactory(enable_memory=False, verbose=False)

        mock_llm = Mock()
        mock_tools = [Mock(), Mock()]

        agent = factory.create_agent(
            role="Test Analyst",
            goal="Analyze test data",
            backstory="Expert test analyst",
            llm=mock_llm,
            tools=mock_tools,
        )

        # Verify Agent constructor was called
        assert mock_agent_class.called
        assert agent is not None

        # Get the kwargs passed to Agent constructor
        call_kwargs = mock_agent_class.call_args[1]

        # Verify defaults were applied
        assert call_kwargs["role"] == "Test Analyst"
        assert call_kwargs["goal"] == "Analyze test data"
        assert call_kwargs["backstory"] == "Expert test analyst"
        assert call_kwargs["allow_delegation"] is False
        assert call_kwargs["max_iter"] == 1
        assert call_kwargs["verbose"] is False
        assert call_kwargs["llm"] == mock_llm
        assert call_kwargs["tools"] == mock_tools

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Agent")
    def test_create_agent_with_overrides(self, mock_agent_class):
        """Test agent creation with explicit overrides."""
        factory = CrewFactory(enable_memory=False)

        agent = factory.create_agent(
            role="Test Analyst",
            goal="Analyze test data",
            backstory="Expert test analyst",
            allow_delegation=True,  # Override default
            max_iter=5,  # Override default
            verbose=True,  # Override default
        )

        assert agent is not None
        call_kwargs = mock_agent_class.call_args[1]

        # Verify overrides were applied
        assert call_kwargs["allow_delegation"] is True
        assert call_kwargs["max_delegation"] == 1
        assert call_kwargs["max_iter"] == 5
        assert call_kwargs["verbose"] is True

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Crew")
    def test_create_crew_with_defaults(self, mock_crew_class):
        """Test crew creation with default configuration."""
        factory = CrewFactory(enable_memory=False, verbose=False)

        mock_agents = [Mock(), Mock()]
        mock_tasks = [Mock(), Mock()]

        crew = factory.create_crew(
            agents=mock_agents,
            tasks=mock_tasks,
        )

        assert mock_crew_class.called
        assert crew is not None

        call_kwargs = mock_crew_class.call_args[1]

        # Verify defaults were applied
        assert call_kwargs["agents"] == mock_agents
        assert call_kwargs["tasks"] == mock_tasks
        assert call_kwargs["max_iterations"] == 1
        assert call_kwargs["verbose"] is False
        assert call_kwargs["embedder"] is None  # Memory disabled

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Crew")
    def test_create_crew_with_overrides(self, mock_crew_class):
        """Test crew creation with explicit overrides."""
        factory = CrewFactory(enable_memory=False)

        mock_agents = [Mock()]
        mock_tasks = [Mock()]

        crew = factory.create_crew(
            agents=mock_agents,
            tasks=mock_tasks,
            max_execution_time=1800,  # Override default
            max_iterations=3,  # Override default
            verbose=True,  # Override default
        )

        assert crew is not None
        call_kwargs = mock_crew_class.call_args[1]

        # Verify overrides were applied
        assert call_kwargs["max_execution_time"] == 1800
        assert call_kwargs["max_iterations"] == 3
        assert call_kwargs["verbose"] is True

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Task")
    def test_create_task(self, mock_task_class):
        """Test task creation."""
        factory = CrewFactory()

        mock_agent = Mock()

        task = factory.create_task(
            description="Test task description",
            agent=mock_agent,
            expected_output="Test output",
        )

        assert mock_task_class.called
        assert task is not None

        call_kwargs = mock_task_class.call_args[1]

        assert call_kwargs["description"] == "Test task description"
        assert call_kwargs["agent"] == mock_agent
        assert call_kwargs["expected_output"] == "Test output"
        assert call_kwargs["async_execution"] is False


class TestCrewMemoryManager:
    """Test CrewMemoryManager configuration."""

    def test_is_memory_enabled_default(self):
        """Test memory enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert CrewMemoryManager.is_memory_enabled() is True

    def test_is_memory_disabled_via_env(self):
        """Test memory can be disabled via environment variable."""
        with patch.dict(os.environ, {"CREWAI_DISABLE_MEMORY": "true"}):
            assert CrewMemoryManager.is_memory_enabled() is False

    def test_get_memory_config_disabled(self):
        """Test memory config when disabled."""
        config = CrewMemoryManager.get_memory_config()

        if not CrewMemoryManager.is_memory_enabled():
            assert config["memory"] is False
        else:
            assert config["memory"] is True


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("app.services.crewai_flows.config.crew_factory.default_factory")
    def test_create_agent_convenience(self, mock_factory):
        """Test create_agent convenience function."""
        mock_factory.create_agent.return_value = Mock()

        agent = create_agent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        assert mock_factory.create_agent.called
        assert agent is not None

    @patch("app.services.crewai_flows.config.crew_factory.default_factory")
    def test_create_crew_convenience(self, mock_factory):
        """Test create_crew convenience function."""
        mock_factory.create_crew.return_value = Mock()

        crew = create_crew(
            agents=[Mock()],
            tasks=[Mock()],
        )

        assert mock_factory.create_crew.called
        assert crew is not None

    @patch("app.services.crewai_flows.config.crew_factory.default_factory")
    def test_create_task_convenience(self, mock_factory):
        """Test create_task convenience function."""
        mock_factory.create_task.return_value = Mock()

        task = create_task(
            description="Test",
            agent=Mock(),
            expected_output="Test output",
        )

        assert mock_factory.create_task.called
        assert task is not None


class TestBackwardCompatibility:
    """Test that the factory pattern maintains expected behavior."""

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Agent")
    def test_no_delegation_default(self, mock_agent_class):
        """Test that agents still have no delegation by default."""
        agent = create_agent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        assert agent is not None
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["allow_delegation"] is False
        assert call_kwargs["max_delegation"] == 0

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Agent")
    def test_single_iteration_default(self, mock_agent_class):
        """Test that agents still have single iteration by default."""
        agent = create_agent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        assert agent is not None
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["max_iter"] == 1

    @patch("app.services.crewai_flows.config.crew_factory.CREWAI_AVAILABLE", True)
    @patch("app.services.crewai_flows.config.crew_factory.Crew")
    def test_crew_timeout_default(self, mock_crew_class):
        """Test that crews still have proper timeout by default."""
        crew = create_crew(
            agents=[Mock()],
            tasks=[Mock()],
        )

        assert crew is not None
        call_kwargs = mock_crew_class.call_args[1]
        assert call_kwargs["max_execution_time"] > 0
        # Default should be 600 seconds (10 minutes) unless env override
        assert call_kwargs["max_execution_time"] >= 600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
