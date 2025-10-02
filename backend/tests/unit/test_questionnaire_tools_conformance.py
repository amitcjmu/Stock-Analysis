"""
Unit tests for questionnaire generation tools conformance with CrewAI BaseTool.

These tests ensure that all questionnaire generation tools properly inherit from
BaseTool and can be used with CrewAI agents without validation errors.
"""

import pytest
from crewai import Agent
from crewai.tools import BaseTool

from app.services.ai_analysis.questionnaire_generator.tools.utils import (
    create_gap_analysis_tools,
    create_questionnaire_generation_tools,
)
from app.services.ai_analysis.questionnaire_generator.tools.analysis import (
    GapAnalysisTool,
)
from app.services.ai_analysis.questionnaire_generator.tools.validation import (
    AssetIntelligenceTool,
)
from app.services.ai_analysis.questionnaire_generator.tools.generation import (
    QuestionnaireGenerationTool,
)


class TestToolConformance:
    """Test that all questionnaire tools conform to CrewAI BaseTool requirements."""

    def test_gap_analysis_tool_is_basetool(self):
        """Test that GapAnalysisTool inherits from BaseTool."""
        tool = GapAnalysisTool()
        assert isinstance(tool, BaseTool), "GapAnalysisTool must inherit from BaseTool"

    def test_asset_intelligence_tool_is_basetool(self):
        """Test that AssetIntelligenceTool inherits from BaseTool."""
        tool = AssetIntelligenceTool()
        assert isinstance(
            tool, BaseTool
        ), "AssetIntelligenceTool must inherit from BaseTool"

    def test_questionnaire_generation_tool_is_basetool(self):
        """Test that QuestionnaireGenerationTool inherits from BaseTool."""
        tool = QuestionnaireGenerationTool()
        assert isinstance(
            tool, BaseTool
        ), "QuestionnaireGenerationTool must inherit from BaseTool"

    def test_gap_analysis_factory_returns_basetool_instances(self):
        """Test that create_gap_analysis_tools returns only BaseTool instances."""
        tools = create_gap_analysis_tools()
        assert len(tools) > 0, "Factory should return at least one tool"
        assert all(
            isinstance(t, BaseTool) for t in tools
        ), "All tools must be BaseTool instances"

    def test_questionnaire_generation_factory_returns_basetool_instances(self):
        """Test that create_questionnaire_generation_tools returns only BaseTool instances."""
        tools = create_questionnaire_generation_tools()
        assert len(tools) > 0, "Factory should return at least one tool"
        assert all(
            isinstance(t, BaseTool) for t in tools
        ), "All tools must be BaseTool instances"

    def test_gap_analysis_tool_has_args_schema(self):
        """Test that GapAnalysisTool has a valid args_schema."""
        tool = GapAnalysisTool()
        assert hasattr(tool, "args_schema"), "Tool must have args_schema attribute"
        assert tool.args_schema is not None, "args_schema must not be None"

    def test_asset_intelligence_tool_has_args_schema(self):
        """Test that AssetIntelligenceTool has a valid args_schema."""
        tool = AssetIntelligenceTool()
        assert hasattr(tool, "args_schema"), "Tool must have args_schema attribute"
        assert tool.args_schema is not None, "args_schema must not be None"

    def test_questionnaire_generation_tool_has_args_schema(self):
        """Test that QuestionnaireGenerationTool has a valid args_schema."""
        tool = QuestionnaireGenerationTool()
        assert hasattr(tool, "args_schema"), "Tool must have args_schema attribute"
        assert tool.args_schema is not None, "args_schema must not be None"


class TestAgentIntegration:
    """Test that tools can be used with CrewAI Agent without validation errors."""

    def test_agent_accepts_gap_analysis_tools(self):
        """Test that Agent accepts gap analysis tools without Pydantic validation errors."""
        tools = create_gap_analysis_tools()

        # This should not raise a Pydantic ValidationError
        agent = Agent(
            role="business_value_analyst",
            goal="Analyze business value and data gaps",
            backstory="Expert in business value analysis and gap assessment",
            tools=tools,
            verbose=False,
        )

        assert agent is not None, "Agent should be created successfully"
        assert len(agent.tools) > 0, "Agent should have tools configured"

    def test_agent_accepts_questionnaire_generation_tools(self):
        """Test that Agent accepts questionnaire generation tools without validation errors."""
        tools = create_questionnaire_generation_tools()

        # This should not raise a Pydantic ValidationError
        agent = Agent(
            role="questionnaire_generator",
            goal="Generate adaptive questionnaires based on gaps",
            backstory="Expert in creating contextual questionnaires",
            tools=tools,
            verbose=False,
        )

        assert agent is not None, "Agent should be created successfully"
        assert len(agent.tools) > 0, "Agent should have tools configured"

    def test_agent_with_mixed_tools(self):
        """Test that Agent accepts a mix of gap analysis and questionnaire tools."""
        gap_tools = create_gap_analysis_tools()
        questionnaire_tools = create_questionnaire_generation_tools()
        all_tools = gap_tools + questionnaire_tools

        # This should not raise a Pydantic ValidationError
        agent = Agent(
            role="comprehensive_analyst",
            goal="Perform comprehensive analysis and questionnaire generation",
            backstory="Expert in both analysis and questionnaire design",
            tools=all_tools,
            verbose=False,
        )

        assert agent is not None, "Agent should be created successfully"
        assert len(agent.tools) >= len(gap_tools) + len(
            questionnaire_tools
        ), "Agent should have all tools configured"


class TestToolMetadata:
    """Test that tools have proper metadata defined."""

    def test_gap_analysis_tool_metadata(self):
        """Test that GapAnalysisTool has proper name and description."""
        tool = GapAnalysisTool()
        assert hasattr(tool, "name"), "Tool must have name attribute"
        assert hasattr(tool, "description"), "Tool must have description attribute"
        assert tool.name == "gap_analysis", "Tool name should be 'gap_analysis'"
        assert len(tool.description) > 0, "Tool description should not be empty"

    def test_asset_intelligence_tool_metadata(self):
        """Test that AssetIntelligenceTool has proper name and description."""
        tool = AssetIntelligenceTool()
        assert hasattr(tool, "name"), "Tool must have name attribute"
        assert hasattr(tool, "description"), "Tool must have description attribute"
        assert (
            tool.name == "asset_intelligence"
        ), "Tool name should be 'asset_intelligence'"
        assert len(tool.description) > 0, "Tool description should not be empty"

    def test_questionnaire_generation_tool_metadata(self):
        """Test that QuestionnaireGenerationTool has proper name and description."""
        tool = QuestionnaireGenerationTool()
        assert hasattr(tool, "name"), "Tool must have name attribute"
        assert hasattr(tool, "description"), "Tool must have description attribute"
        assert (
            tool.name == "questionnaire_generation"
        ), "Tool name should be 'questionnaire_generation'"
        assert len(tool.description) > 0, "Tool description should not be empty"
