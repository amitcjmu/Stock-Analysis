"""
Flow Status Service for Discovery Flow Operations

This service handles status checking and updates for discovery flows.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.utils.flow_constants.flow_states import FlowType, FlowStatus
from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def get_flow_status(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Dict[str, Any]:
    """Get the status of a discovery flow."""
    # First try to get from DiscoveryFlow
    stmt = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    discovery_flow = result.scalar_one_or_none()

    if discovery_flow:
        logger.info(
            safe_log_format(
                "🔍 Executing DiscoveryFlow query with flow_id={flow_id}, "
                "client={client_account_id}, engagement={engagement_id}",
                flow_id=flow_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
            )
        )

        # Get flow details directly
        flow_result = await db.execute(
            select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
        )
        discovery_flow = flow_result.scalar_one_or_none()

        if discovery_flow:
            logger.info(
                safe_log_format(
                    "✅ Discovery flow found: {flow_id} with status={status}",
                    flow_id=flow_id,
                    status=discovery_flow.status,
                )
            )

            # Get additional data from CrewAI Flow State if available
            master_result = await db.execute(
                select(CrewAIFlowStateExtensions).where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_id,
                        CrewAIFlowStateExtensions.client_account_id
                        == context.client_account_id,
                        CrewAIFlowStateExtensions.engagement_id
                        == context.engagement_id,
                    )
                )
            )
            master_flow = master_result.scalar_one_or_none()

            phase_state = discovery_flow.phase_state or {}
            if master_flow and master_flow.flow_persistence_data:
                # Extract phase state from flow persistence data
                master_phase_state = master_flow.flow_persistence_data.get(
                    "current_phase_state", {}
                )
                if master_phase_state:
                    phase_state.update(master_phase_state)

            # Ensure all data is JSON serializable to avoid recursion errors
            safe_metadata = {}
            if discovery_flow.metadata:
                try:
                    # Only include basic types to avoid circular references
                    import json

                    safe_metadata = json.loads(json.dumps(discovery_flow.metadata))
                except (TypeError, ValueError, RecursionError):
                    safe_metadata = {"error": "metadata_serialization_failed"}

            safe_phase_state = {}
            if phase_state:
                try:
                    import json

                    safe_phase_state = json.loads(json.dumps(phase_state))
                except (TypeError, ValueError, RecursionError):
                    safe_phase_state = {"error": "phase_state_serialization_failed"}

            safe_phases_completed = {}
            if discovery_flow.phases_completed:
                try:
                    import json

                    safe_phases_completed = json.loads(
                        json.dumps(discovery_flow.phases_completed)
                    )
                except (TypeError, ValueError, RecursionError):
                    safe_phases_completed = {
                        "error": "phases_completed_serialization_failed"
                    }

            return {
                "flow_id": flow_id,
                "status": discovery_flow.status,
                "current_phase": discovery_flow.current_phase,
                "progress": discovery_flow.progress_percentage or 0,
                "phase_state": safe_phase_state,
                "metadata": safe_metadata,
                "last_activity": (
                    discovery_flow.updated_at.isoformat()
                    if discovery_flow.updated_at
                    else None
                ),
                "error_message": discovery_flow.error_message,
                "phase_completion": safe_phases_completed,
            }

    # Debug: Check if flow exists but with different context
    debug_stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
    debug_result = await db.execute(debug_stmt)
    debug_flow = debug_result.scalar_one_or_none()

    if debug_flow:
        logger.error(
            safe_log_format(
                "❌ Flow {flow_id} exists but with different context: "
                "client={client_account_id}, engagement={engagement_id}",
                flow_id=flow_id,
                client_account_id=debug_flow.client_account_id,
                engagement_id=debug_flow.engagement_id,
            )
        )
        raise ValueError(f"Flow {flow_id} exists but not in current context")
    else:
        logger.error(
            safe_log_format(
                "❌ Flow {flow_id} not found in DiscoveryFlow table with context "
                "client={client_account_id}, engagement={engagement_id}",
                flow_id=flow_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
            )
        )
        raise ValueError(f"Flow {flow_id} not found")


async def update_flow_status(
    flow_id: str,
    status: str,
    db: AsyncSession,
    context: RequestContext,
    current_phase: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update the status of a discovery flow."""
    stmt = update(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )

    update_values = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }

    if current_phase is not None:
        update_values["current_phase"] = current_phase

    if error_message is not None:
        update_values["error_message"] = error_message

    if metadata is not None:
        update_values["metadata"] = metadata

    stmt = stmt.values(**update_values)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise ValueError(f"Flow {flow_id} not found or not in current context")

    return {
        "flow_id": flow_id,
        "status": status,
        "current_phase": current_phase,
        "updated": True,
    }


async def get_active_flows(
    db: AsyncSession, context: RequestContext, limit: int = 10
) -> List[Dict[str, Any]]:
    """Get active discovery flows for the current context."""
    # Query for active flows with proper status filtering
    stmt = (
        select(DiscoveryFlow)
        .where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status.in_(
                    [
                        FlowStatus.INITIALIZING.value,
                        FlowStatus.RUNNING.value,
                        FlowStatus.RUNNING.value,  # processing mapped to running
                        FlowStatus.PAUSED.value,
                        FlowStatus.WAITING.value,
                    ]
                ),
            )
        )
        .order_by(desc(DiscoveryFlow.updated_at))
        .limit(limit)
    )

    result = await db.execute(stmt)
    flows = result.scalars().all()

    # Also check CrewAI Flow State for active flows
    master_stmt = (
        select(CrewAIFlowStateExtensions)
        .where(
            and_(
                CrewAIFlowStateExtensions.client_account_id
                == context.client_account_id,
                CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                CrewAIFlowStateExtensions.flow_type == FlowType.DISCOVERY.value,
                CrewAIFlowStateExtensions.flow_status.in_(
                    [
                        FlowStatus.INITIALIZING.value,
                        FlowStatus.RUNNING.value,
                        FlowStatus.WAITING.value,
                        FlowStatus.PAUSED.value,
                    ]
                ),
            )
        )
        .order_by(desc(CrewAIFlowStateExtensions.updated_at))
        .limit(limit)
    )

    master_result = await db.execute(master_stmt)
    master_flows = master_result.scalars().all()

    # Combine and deduplicate flows
    flow_ids_seen = set()
    active_flows = []

    for flow in flows:
        if flow.flow_id not in flow_ids_seen:
            flow_ids_seen.add(flow.flow_id)
            active_flows.append(
                {
                    "flow_id": flow.flow_id,
                    "flow_name": flow.flow_name,
                    "status": flow.status,
                    "current_phase": flow.current_phase,
                    "progress": flow.progress_percentage or 0,
                    "created_at": (
                        flow.created_at.isoformat() if flow.created_at else None
                    ),
                    "updated_at": (
                        flow.updated_at.isoformat() if flow.updated_at else None
                    ),
                    "source": "discovery_flow",
                }
            )

    for master_flow in master_flows:
        if master_flow.flow_id not in flow_ids_seen:
            flow_ids_seen.add(master_flow.flow_id)
            active_flows.append(
                {
                    "flow_id": master_flow.flow_id,
                    "flow_name": getattr(master_flow, "flow_name", "Unnamed Flow"),
                    "status": getattr(master_flow, "flow_status", "unknown"),
                    "current_phase": getattr(master_flow, "current_phase", None),
                    "progress": getattr(master_flow, "progress_percentage", 0) or 0,
                    "created_at": (
                        master_flow.created_at.isoformat()
                        if getattr(master_flow, "created_at", None)
                        else None
                    ),
                    "updated_at": (
                        master_flow.updated_at.isoformat()
                        if getattr(master_flow, "updated_at", None)
                        else None
                    ),
                    "source": "crewai_flow",
                }
            )

    logger.info(
        safe_log_format(
            "Found {count} active flows for client={client_account_id}, "
            "engagement={engagement_id}",
            count=len(active_flows),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )
    )

    return active_flows
