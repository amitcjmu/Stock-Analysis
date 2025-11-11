"""
Example Usage: DecommissionAgentPool Integration

This file demonstrates how to integrate DecommissionAgentPool with child flow services
for decommission phase execution.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, List

from app.services.agents.decommission import DecommissionAgentPool

logger = logging.getLogger(__name__)


async def execute_decommission_planning_phase(
    client_account_id: str,
    engagement_id: str,
    system_ids: List[str],
    decommission_strategy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Example: Execute decommission planning phase using agent pool.

    This demonstrates the pattern for Phase 1 (decommission_planning) per FlowTypeConfig.

    Args:
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        system_ids: List of system IDs to decommission
        decommission_strategy: Strategy configuration

    Returns:
        Planning phase results from crew execution
    """
    try:
        # Initialize agent pool
        agent_pool = DecommissionAgentPool()

        # Get required agents for planning phase
        logger.info(f"Getting agents for {len(system_ids)} systems")

        agents = {}
        for agent_key in [
            "system_analysis_agent",
            "dependency_mapper_agent",
            "data_retention_agent",
        ]:
            agents[agent_key] = await agent_pool.get_agent(
                agent_key=agent_key,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                tools=[],  # Add actual tools here based on agent_key
            )

        # Create planning crew
        logger.info("Creating decommission planning crew")
        crew = agent_pool.create_decommission_planning_crew(
            agents=agents,
            system_ids=system_ids,
            decommission_strategy=decommission_strategy,
        )

        if not crew:
            logger.error("Failed to create planning crew")
            return {
                "status": "failed",
                "error": "Crew creation failed - CrewAI unavailable",
            }

        # Execute crew
        logger.info("Executing planning crew")
        result = crew.kickoff()

        # Process results
        logger.info("Planning phase completed successfully")

        # Store learnings using TenantMemoryManager (per ADR-024)
        # from app.services.crewai_flows.memory.tenant_memory_manager import (
        #     TenantMemoryManager,
        #     LearningScope,
        # )
        #
        # memory_manager = TenantMemoryManager(...)
        # await memory_manager.store_learning(
        #     client_account_id=UUID(client_account_id),
        #     engagement_id=UUID(engagement_id),
        #     scope=LearningScope.ENGAGEMENT,
        #     pattern_type="decommission_planning",
        #     pattern_data={
        #         "system_count": len(system_ids),
        #         "strategy": decommission_strategy,
        #         "dependencies_found": result.get("dependency_count", 0),
        #     },
        # )

        return {
            "status": "completed",
            "phase": "decommission_planning",
            "system_count": len(system_ids),
            "results": result,
        }

    except Exception as e:
        logger.error(f"Planning phase execution failed: {e}")
        return {"status": "failed", "error": str(e)}

    finally:
        # Release agents when done
        await agent_pool.release_agents(client_account_id, engagement_id)


async def execute_data_migration_phase(
    client_account_id: str,
    engagement_id: str,
    retention_policies: Dict[str, Any],
    system_ids: List[str],
) -> Dict[str, Any]:
    """
    Example: Execute data migration phase using agent pool.

    This demonstrates the pattern for Phase 2 (data_migration) per FlowTypeConfig.

    Args:
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        retention_policies: Policies from planning phase
        system_ids: List of system IDs

    Returns:
        Data migration phase results from crew execution
    """
    try:
        agent_pool = DecommissionAgentPool()

        # Get required agents for data migration phase
        agents = {}
        for agent_key in [
            "data_retention_agent",
            "compliance_agent",
            "validation_agent",
        ]:
            agents[agent_key] = await agent_pool.get_agent(
                agent_key=agent_key,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                tools=[],
            )

        # Create data migration crew
        crew = agent_pool.create_data_migration_crew(
            agents=agents, retention_policies=retention_policies, system_ids=system_ids
        )

        if not crew:
            return {"status": "failed", "error": "Crew creation failed"}

        # Execute crew
        result = crew.kickoff()

        return {
            "status": "completed",
            "phase": "data_migration",
            "system_count": len(system_ids),
            "results": result,
        }

    except Exception as e:
        logger.error(f"Data migration phase failed: {e}")
        return {"status": "failed", "error": str(e)}

    finally:
        await agent_pool.release_agents(client_account_id, engagement_id)


async def execute_system_shutdown_phase(
    client_account_id: str,
    engagement_id: str,
    decommission_plan: Dict[str, Any],
    system_ids: List[str],
) -> Dict[str, Any]:
    """
    Example: Execute system shutdown phase using agent pool.

    This demonstrates the pattern for Phase 3 (system_shutdown) per FlowTypeConfig.
    Includes validation and rollback capabilities.

    Args:
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        decommission_plan: Plan from planning phase
        system_ids: List of system IDs

    Returns:
        System shutdown phase results from crew execution
    """
    try:
        agent_pool = DecommissionAgentPool()

        # Get required agents for shutdown phase
        agents = {}
        for agent_key in [
            "shutdown_orchestrator_agent",
            "validation_agent",
            "rollback_agent",
        ]:
            agents[agent_key] = await agent_pool.get_agent(
                agent_key=agent_key,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                tools=[],
            )

        # Create shutdown crew
        crew = agent_pool.create_system_shutdown_crew(
            agents=agents, decommission_plan=decommission_plan, system_ids=system_ids
        )

        if not crew:
            return {"status": "failed", "error": "Crew creation failed"}

        # Execute crew
        result = crew.kickoff()

        # Check validation results
        validation_status = result.get("validation_results", {}).get("status")

        if validation_status == "failed":
            logger.warning("Validation failed - rollback may be required")
            return {
                "status": "validation_failed",
                "phase": "system_shutdown",
                "rollback_available": True,
                "results": result,
            }

        return {
            "status": "completed",
            "phase": "system_shutdown",
            "system_count": len(system_ids),
            "results": result,
        }

    except Exception as e:
        logger.error(f"System shutdown phase failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "rollback_available": True,
        }

    finally:
        await agent_pool.release_agents(client_account_id, engagement_id)


# Full workflow example
async def complete_decommission_workflow_example(
    client_account_id: str,
    engagement_id: str,
    system_ids: List[str],
    decommission_strategy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Example: Complete decommission workflow using all 3 phases.

    This demonstrates the full decommission flow execution pattern.

    Args:
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        system_ids: List of system IDs to decommission
        decommission_strategy: Strategy configuration

    Returns:
        Complete workflow results
    """
    workflow_results = {"phases": {}}

    try:
        # Phase 1: Decommission Planning
        logger.info("Starting Phase 1: Decommission Planning")
        planning_result = await execute_decommission_planning_phase(
            client_account_id, engagement_id, system_ids, decommission_strategy
        )

        workflow_results["phases"]["decommission_planning"] = planning_result

        if planning_result["status"] != "completed":
            logger.error("Planning phase failed, aborting workflow")
            return {"status": "failed_at_planning", "results": workflow_results}

        # Phase 2: Data Migration
        logger.info("Starting Phase 2: Data Migration")
        retention_policies = planning_result["results"].get("retention_policies", {})

        migration_result = await execute_data_migration_phase(
            client_account_id, engagement_id, retention_policies, system_ids
        )

        workflow_results["phases"]["data_migration"] = migration_result

        if migration_result["status"] != "completed":
            logger.error("Data migration failed, aborting workflow")
            return {"status": "failed_at_migration", "results": workflow_results}

        # Phase 3: System Shutdown
        logger.info("Starting Phase 3: System Shutdown")
        decommission_plan = planning_result["results"].get("decommission_plan", {})

        shutdown_result = await execute_system_shutdown_phase(
            client_account_id, engagement_id, decommission_plan, system_ids
        )

        workflow_results["phases"]["system_shutdown"] = shutdown_result

        if shutdown_result["status"] == "validation_failed":
            logger.warning("Shutdown validation failed - review required")
            return {"status": "validation_failed", "results": workflow_results}

        if shutdown_result["status"] != "completed":
            logger.error("System shutdown failed")
            return {"status": "failed_at_shutdown", "results": workflow_results}

        # Success!
        logger.info("Decommission workflow completed successfully")
        return {
            "status": "completed",
            "systems_decommissioned": len(system_ids),
            "results": workflow_results,
        }

    except Exception as e:
        logger.error(f"Decommission workflow failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "results": workflow_results,
        }
