"""
Helper functions for phase persistence and completion updates.

Extracted from flow_execution_service.py to reduce complexity and file length.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands,
)

logger = logging.getLogger(__name__)


async def persist_phase_completion(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    phase_name: str,
    result: Dict[str, Any],
) -> None:
    """
    Persist phase completion and update flow state.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        phase_name: Name of the completed phase
        result: Execution result from MFO
    """
    try:
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )

        # Extract phase data and agent insights from the result
        phase_data = result.get("result", {}).get("crew_results", {}) or {}
        agent_insights = extract_agent_insights(result)

        # Call update_phase_completion to persist phase completion
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase=phase_name,
            data=phase_data,
            completed=True,
            agent_insights=agent_insights,
        )

        logger.info(
            safe_log_format(
                "✅ Phase completion persisted: flow_id={flow_id}, phase={phase}",
                flow_id=mask_id(str(flow_id)),
                phase=phase_name,
            )
        )

        # Update current_phase to next_phase if provided
        next_phase = extract_next_phase(result)
        if next_phase:
            await advance_flow_phase(db, context, flow_id, phase_name, next_phase)

    except Exception as persistence_error:
        logger.error(
            safe_log_format(
                "❌ Failed to persist phase completion: flow_id={flow_id}, phase={phase}, error={error}",
                flow_id=mask_id(str(flow_id)),
                phase=phase_name,
                error=str(persistence_error),
            )
        )
        # Don't fail the main execution if persistence fails


async def persist_field_mapping_completion(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    result: Any,
) -> None:
    """
    Persist field mapping phase completion.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        result: Phase execution result
    """
    try:
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )

        # Call update_phase_completion to persist field mapping completion
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase="field_mapping",
            data=result.data if hasattr(result, "data") else {},
            completed=True,
            agent_insights=[
                {
                    "type": "completion",
                    "content": "Field mapping phase completed successfully",
                }
            ],
        )

        logger.info(
            safe_log_format(
                "✅ Field mapping completion persisted: flow_id={flow_id}",
                flow_id=mask_id(str(flow_id)),
            )
        )

    except Exception as persistence_error:
        logger.error(
            safe_log_format(
                "❌ Failed to persist field mapping completion: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(persistence_error),
            )
        )
        # Don't fail the main execution if persistence fails


def extract_agent_insights(result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract agent insights from execution result.

    Args:
        result: Execution result dictionary

    Returns:
        List of agent insight dictionaries
    """
    agent_insights = []

    # Check for direct agent_insights in phase data
    phase_data = result.get("result", {}).get("crew_results", {}) or {}
    if "agent_insights" in phase_data:
        agent_insights = phase_data["agent_insights"]
    elif "crew_results" in result.get("result", {}) and isinstance(
        result["result"]["crew_results"], dict
    ):
        crew_results = result["result"]["crew_results"]
        if "message" in crew_results:
            agent_insights = [
                {"type": "completion", "content": crew_results["message"]}
            ]

    return agent_insights


def extract_next_phase(result: Dict[str, Any]) -> Optional[str]:
    """
    Extract next phase from execution result.

    Args:
        result: Execution result dictionary

    Returns:
        Next phase name if available
    """
    # Check multiple locations for next_phase
    next_phase = result.get("result", {}).get("next_phase")
    if not next_phase:
        next_phase = result.get("next_phase")

    return next_phase


async def advance_flow_phase(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    from_phase: str,
    to_phase: str,
) -> None:
    """
    Advance the flow to the next phase.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        from_phase: Current phase name
        to_phase: Next phase name
    """
    try:
        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
            .values(current_phase=to_phase)
        )

        await db.execute(stmt)
        await db.commit()

        logger.info(
            safe_log_format(
                "✅ Flow phase advanced: flow_id={flow_id}, from={from_phase} to={to_phase}",
                flow_id=mask_id(str(flow_id)),
                from_phase=from_phase,
                to_phase=to_phase,
            )
        )

    except Exception as phase_update_error:
        logger.error(
            safe_log_format(
                "❌ Failed to advance flow phase: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(phase_update_error),
            )
        )
        # Don't fail the main execution if phase update fails
