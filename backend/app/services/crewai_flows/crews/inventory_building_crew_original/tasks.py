"""
Inventory Building Tasks - Task Creation Logic

This module contains task creation functions for the Inventory Building Crew.
It implements a robust, sequential-then-parallel task structure:
1. Triage: Fast initial sorting of all assets into domains
2. Classify: Parallel deep classification by domain experts
3. Consolidate: Final assembly and relationship mapping
"""

import logging
from typing import Any, Dict, List

from app.services.crewai_flows.config.crew_factory import create_task

logger = logging.getLogger(__name__)


def create_inventory_tasks(
    agents: list,
    cleaned_data: List[Dict[str, Any]],
    field_mappings: Dict[str, Any],
) -> list:
    """
    Create a robust, sequential-then-parallel task structure for inventory building.

    Task Flow:
    1. Triage Task (Manager): Fast sorting of assets into domains
    2. Parallel Classification Tasks (Experts): Deep domain-specific analysis
       - Server Classification
       - Application Classification
       - Device Classification
    3. Consolidation Task (Manager): Assembly and relationship mapping

    Args:
        agents: List of agent instances [manager, server_expert, app_expert, device_expert]
        cleaned_data: List of cleaned asset records to classify
        field_mappings: Field mapping configuration

    Returns:
        List of task instances in execution order
    """
    manager, server_expert, app_expert, device_expert = agents

    # Step 1: The Triage Task
    # A single, fast task for the manager to sort assets into domains.
    triage_task = create_task(
        description=(
            "Triage the entire list of assets. Your job is to sort each asset "
            "into one of three lists: 'servers', 'applications', or 'devices' "
            "based on its name and type. Do NOT perform a deep classification. "
            "Your output must be a JSON object with these three keys."
        ),
        expected_output=(
            "A JSON object with three keys: 'server_assets', "
            "'application_assets', and 'device_assets'. Each key should "
            "contain a list of the corresponding asset records."
        ),
        agent=manager,
    )

    # Step 2: Parallel Classification Tasks
    # These tasks depend on the triage_task and run in parallel.
    server_classification_task = create_task(
        description=(
            "Perform a detailed classification of the server assets provided. "
            "Identify OS, function, and virtual/physical status.\n\n"
            "CRITICAL: Each asset in your output MUST have an 'asset_type' "
            "field set to exactly 'server'. Add this field to each asset "
            "record if it doesn't exist."
        ),
        expected_output=(
            "A JSON list of fully classified server assets with detailed "
            "attributes. Each asset MUST have asset_type: 'server'."
        ),
        agent=server_expert,
        context=[triage_task],  # Depends on the output of the triage task
        async_execution=True,
    )

    app_classification_task = create_task(
        description=(
            "Perform a detailed classification of the application assets "
            "provided. Identify version, type, and business context.\n\n"
            "CRITICAL: Each asset in your output MUST have an 'asset_type' "
            "field set to exactly 'application'. Add this field to each "
            "asset record if it doesn't exist."
        ),
        expected_output=(
            "A JSON list of fully classified application assets with "
            "detailed attributes. Each asset MUST have asset_type: "
            "'application'."
        ),
        agent=app_expert,
        context=[triage_task],
        async_execution=True,
    )

    device_classification_task = create_task(
        description=(
            "Perform a detailed classification of the device assets "
            "provided. Identify device type and network role.\n\n"
            "CRITICAL: Each asset in your output MUST have an 'asset_type' "
            "field set to exactly 'device'. Add this field to each asset "
            "record if it doesn't exist."
        ),
        expected_output=(
            "A JSON list of fully classified device assets with detailed "
            "attributes. Each asset MUST have asset_type: 'device'."
        ),
        agent=device_expert,
        context=[triage_task],
        async_execution=True,
    )

    # Step 3: Final Consolidation and Relationship Mapping
    # This task runs last, after all experts have finished.
    consolidation_task = create_task(
        description=(
            "Consolidate the outputs from the server, application, and device "
            "experts into a single, unified asset inventory.\n\n"
            "CRITICAL DEDUPLICATION STEP:\n"
            "1. BEFORE finalizing the inventory, you MUST use the "
            "asset_deduplication_checker tool\n"
            "2. Pass ALL assets from all categories (servers, applications, "
            "devices) to the tool\n"
            "3. The tool will return only the unique assets that don't "
            "already exist in the database\n"
            "4. Only include the assets returned by the deduplication tool "
            "in your final output\n\n"
            "After deduplication, analyze the consolidated data to map "
            "relationships between the assets."
        ),
        expected_output=(
            "A final JSON object containing three lists: 'servers', "
            "'applications', and 'devices' (only unique assets), and a "
            "fourth list 'relationships' detailing all identified connections."
        ),
        agent=manager,
        context=[
            server_classification_task,
            app_classification_task,
            device_classification_task,
        ],  # Depends on all classification tasks
    )

    logger.info(
        "✅ Created 5 inventory building tasks: triage, 3 parallel classifications, consolidation"
    )

    return [
        triage_task,
        server_classification_task,
        app_classification_task,
        device_classification_task,
        consolidation_task,
    ]


__all__ = ["create_inventory_tasks"]
