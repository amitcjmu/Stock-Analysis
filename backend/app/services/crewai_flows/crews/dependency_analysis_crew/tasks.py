"""
Dependency Analysis Tasks - Task Creation and Crew Configuration

This module contains the task creation logic and crew configuration for the
Dependency Analysis Crew. It defines the sequential analysis tasks for network,
application, and infrastructure dependency mapping.

Tasks:
1. Network Dependency Analysis - Analyzes network topology and connectivity
2. Application Dependency Analysis - Identifies app-to-app dependencies
3. Infrastructure Mapping - Maps infrastructure dependencies and migration sequences
"""

import logging
from typing import Any, Dict, List

from app.services.crewai_flows.config.crew_factory import create_crew, create_task

logger = logging.getLogger(__name__)

# CrewAI types - imported conditionally
try:
    from crewai import Agent, Crew, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Fallback for type hints
    Agent = object  # type: ignore[misc, assignment]
    Task = object  # type: ignore[misc, assignment]
    Crew = object  # type: ignore[misc, assignment]


def create_dependency_analysis_tasks(
    assets_data: List[Dict[str, Any]],
    network_architecture_specialist: Agent,
    application_dependency_analyst: Agent,
    infrastructure_dependency_mapper: Agent,
) -> List[Task]:
    """
    Create tasks for dependency analysis.

    This function creates three sequential tasks that work together to analyze
    dependencies across network, application, and infrastructure layers.

    Args:
        assets_data: List of asset dictionaries to analyze
        network_architecture_specialist: Agent for network analysis
        application_dependency_analyst: Agent for application dependency analysis
        infrastructure_dependency_mapper: Agent for infrastructure mapping

    Returns:
        List of Task instances for dependency analysis
    """
    tasks = []

    # Format asset list for agents - include ID and name only to prevent overwhelming context
    asset_summary = []
    for asset in assets_data[:50]:  # Limit to first 50 assets for context window
        if isinstance(asset, dict):
            asset_summary.append(
                {
                    "id": asset.get("id", "unknown"),
                    "name": asset.get("name", asset.get("asset_name", "Unknown")),
                    "type": asset.get("type", "unknown"),
                }
            )

    # Task 1: Network dependency analysis
    network_analysis_task = create_task(
        description=f"""Analyze network dependencies and topology for {len(assets_data)} REAL assets.

        CRITICAL INSTRUCTIONS:
        - ONLY analyze the actual assets provided below
        - DO NOT invent or create any fictional services
        - If an asset doesn't have clear dependencies, mark it as standalone
        - Use the asset IDs and names exactly as provided

        For each asset:
        1. Check if asset name/description indicates network connectivity
        2. Look for keywords indicating dependencies (API, database, service)
        3. Identify potential port/protocol usage based on asset type
        4. Determine if asset is client, server, or both
        5. Map connectivity patterns between REAL assets only

        REAL Assets to analyze (showing first {len(asset_summary)} of {len(assets_data)}):
        {asset_summary}

        Return analysis as structured data for each asset.""",
        expected_output="""Network dependency analysis containing:
        - Network topology mapping for each asset
        - Port and protocol requirements
        - Network tier identification
        - Complexity assessment
        - Critical path analysis""",
        agent=network_architecture_specialist,
    )
    tasks.append(network_analysis_task)

    # Task 2: Application dependency analysis
    app_dependency_task = create_task(
        description=f"""Analyze application-to-application dependencies based on the network analysis.

        CRITICAL INSTRUCTIONS:
        - ONLY identify dependencies between the {len(assets_data)} REAL assets provided
        - DO NOT create fictional services or applications
        - Base dependencies on asset names and types
        - If unsure about a dependency, don't include it

        Focus on:
        1. Identifying applications from the asset list (type='application')
        2. Finding servers that host these applications
        3. Discovering databases used by applications
        4. Mapping API relationships based on asset names
        5. Identifying shared infrastructure

        For each dependency found, provide:
        - source_id: The ID of the source asset
        - target_id: The ID of the target asset
        - dependency_type: Type of dependency (hosting, database, api, etc)
        - confidence_score: How confident you are (0.0-1.0)
        - is_app_to_app: Boolean indicating if both are applications

        Return results as a JSON array of dependency objects.""",
        expected_output="""Application dependency analysis containing:
        - Upstream dependencies (services this app depends on)
        - Downstream dependencies (services that depend on this app)
        - Peer dependencies (services at the same level)
        - Integration patterns and complexity
        - Data flow mapping""",
        agent=application_dependency_analyst,
        context=[network_analysis_task],
    )
    tasks.append(app_dependency_task)

    # Task 3: Infrastructure dependency mapping and migration sequence
    infrastructure_mapping_task = create_task(
        description=f"""Map infrastructure dependencies and create migration sequence based on
        network and application analysis of {len(assets_data)} REAL assets.

        CRITICAL INSTRUCTIONS:
        - Create a structured JSON output with discovered dependencies
        - Each dependency must reference REAL asset IDs from the provided list
        - DO NOT invent any services or components

        Required JSON output format:
        {{"dependencies": [
            {{
                "source_id": "actual_asset_id",
                "source_name": "actual_asset_name",
                "target_id": "actual_asset_id",
                "target_name": "actual_asset_name",
                "dependency_type": "hosting|database|api|network|storage",
                "confidence_score": 0.0-1.0,
                "is_app_to_app": true/false,
                "description": "Brief description of the dependency"
            }}
        ],
        "migration_groups": [
            {{
                "group_name": "Group 1",
                "asset_ids": ["id1", "id2"],
                "sequence": 1,
                "reason": "Why these should migrate together"
            }}
        ]}}

        Base dependencies on:
        1. Asset types (servers host applications, applications use databases)
        2. Asset names (similar names may indicate relationships)
        3. Common patterns (web servers, app servers, databases)

        Remember: ONLY use assets from the provided list!""",
        expected_output="""A valid JSON object containing:
        1. 'dependencies' array with discovered dependency relationships
        2. 'migration_groups' array with recommended migration sequences
        Each dependency must reference real asset IDs from the provided inventory.""",
        agent=infrastructure_dependency_mapper,
        context=[network_analysis_task, app_dependency_task],
    )
    tasks.append(infrastructure_mapping_task)

    return tasks


def create_dependency_analysis_crew_instance(
    agents: List[Agent], tasks: List[Task]
) -> Crew:
    """
    Create the Dependency Analysis Crew instance.

    This function creates a configured Crew instance with the provided agents
    and tasks, using sequential processing for dependency analysis.

    Args:
        agents: List of Agent instances for the crew
        tasks: List of Task instances for the crew

    Returns:
        Configured Crew instance
    """
    return create_crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process="sequential",
    )


# Export task creation functions
__all__ = [
    "create_dependency_analysis_tasks",
    "create_dependency_analysis_crew_instance",
]
