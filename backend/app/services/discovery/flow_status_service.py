"""
Flow Status Service for Discovery Flow Operations

This service handles status checking and updates for discovery flows.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow, DiscoveryFlowStatus
from app.models.master_flow import MasterFlow, FlowType
from app.core.context import RequestContext
from app.core.logging import safe_log_format

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

            # Get additional data from MasterFlow if available
            master_result = await db.execute(
                select(MasterFlow).where(
                    and_(
                        MasterFlow.flow_id == flow_id,
                        MasterFlow.client_account_id == context.client_account_id,
                        MasterFlow.engagement_id == context.engagement_id,
                    )
                )
            )
            master_flow = master_result.scalar_one_or_none()

            phase_state = discovery_flow.phase_state or {}
            if master_flow and master_flow.current_phase_state:
                phase_state.update(master_flow.current_phase_state)

            return {
                "flow_id": flow_id,
                "status": discovery_flow.status,
                "current_phase": discovery_flow.current_phase,
                "progress": discovery_flow.progress or 0,
                "phase_state": phase_state,
                "metadata": discovery_flow.metadata,
                "last_activity": (
                    discovery_flow.updated_at.isoformat()
                    if discovery_flow.updated_at
                    else None
                ),
                "error_message": discovery_flow.error_message,
                "phase_completion": discovery_flow.phase_completion,
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
                        DiscoveryFlowStatus.INITIALIZED.value,
                        DiscoveryFlowStatus.RUNNING.value,
                        DiscoveryFlowStatus.PROCESSING.value,
                        DiscoveryFlowStatus.PAUSED.value,
                        DiscoveryFlowStatus.WAITING_FOR_APPROVAL.value,
                    ]
                ),
            )
        )
        .order_by(desc(DiscoveryFlow.updated_at))
        .limit(limit)
    )

    result = await db.execute(stmt)
    flows = result.scalars().all()

    # Also check MasterFlow for active flows
    master_stmt = (
        select(MasterFlow)
        .where(
            and_(
                MasterFlow.client_account_id == context.client_account_id,
                MasterFlow.engagement_id == context.engagement_id,
                MasterFlow.flow_type == FlowType.DISCOVERY.value,
                MasterFlow.is_active.is_(True),
            )
        )
        .order_by(desc(MasterFlow.updated_at))
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
                    "progress": flow.progress or 0,
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
                    "flow_name": master_flow.flow_name,
                    "status": master_flow.status,
                    "current_phase": master_flow.current_phase,
                    "progress": master_flow.progress or 0,
                    "created_at": (
                        master_flow.created_at.isoformat()
                        if master_flow.created_at
                        else None
                    ),
                    "updated_at": (
                        master_flow.updated_at.isoformat()
                        if master_flow.updated_at
                        else None
                    ),
                    "source": "master_flow",
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
