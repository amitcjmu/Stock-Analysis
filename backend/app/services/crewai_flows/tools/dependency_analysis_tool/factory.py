"""
Factory functions for creating dependency analysis tools.

This module contains factory functions that create the appropriate tool
instances based on whether CrewAI is available or not.
"""

from typing import Any, Dict, List

from .base import CREWAI_TOOLS_AVAILABLE, logger
from .tools import (
    DependencyAnalysisTool,
    DependencyGraphBuilderTool,
    MigrationWavePlannerTool,
    DummyDependencyAnalysisTool,
    DummyDependencyGraphBuilderTool,
    DummyMigrationWavePlannerTool,
)


def create_dependency_analysis_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to analyze dependencies and build dependency graphs

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id

    Returns:
        List of dependency analysis tools
    """
    logger.info("🔧 Creating dependency analysis tools for persistent agents")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Use factory functions to create tools
        analyzer = _create_dependency_analysis_tool(context_info)
        tools.append(analyzer)

        graph_builder = _create_dependency_graph_builder_tool(context_info)
        tools.append(graph_builder)

        wave_planner = _create_migration_wave_planner_tool(context_info)
        tools.append(wave_planner)

        logger.info(f"✅ Created {len(tools)} dependency analysis tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create dependency analysis tools: {e}")
        return []


# Factory functions to create tools
def _create_dependency_analysis_tool(context_info: Dict[str, Any]):
    """Create dependency analysis tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyDependencyAnalysisTool(context_info)
    return DependencyAnalysisTool(context_info)


def _create_dependency_graph_builder_tool(context_info: Dict[str, Any]):
    """Create dependency graph builder tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyDependencyGraphBuilderTool(context_info)
    return DependencyGraphBuilderTool(context_info)


def _create_migration_wave_planner_tool(context_info: Dict[str, Any]):
    """Create migration wave planner tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyMigrationWavePlannerTool(context_info)
    return MigrationWavePlannerTool(context_info)
