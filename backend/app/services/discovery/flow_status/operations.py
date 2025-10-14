"""
Core Operations for Discovery Flow Status Management

This module contains the main public API functions for discovery flow status operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import select, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.utils.flow_constants.flow_states import FlowType, FlowStatus
from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.services.agents.agent_service_layer.handlers.flow_handler_helpers import (
    FlowHandlerHelpers,
)

from .query_helpers import get_discovery_flow, get_master_flow, debug_flow_context
from .data_helpers import (
    build_phase_state,
    safe_serialize,
    load_raw_data,
    load_field_mappings,
    build_summary,
    extract_master_flow_data,
    build_flow_status_response,
)

logger = logging.getLogger(__name__)

# Total number of discovery flow phases for progress calculation
TOTAL_DISCOVERY_PHASES = 6


async def get_flow_status(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Dict[str, Any]:
    """Get the status of a discovery flow."""
    # Get the discovery flow
    discovery_flow = await get_discovery_flow(flow_id, db, context)

    if discovery_flow:
        return await _process_found_flow(flow_id, discovery_flow, db, context)

    # Flow not found - perform debug check
    await debug_flow_context(flow_id, db, context)


async def _process_found_flow(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """Process a found discovery flow and build response"""
    logger.info(
        safe_log_format(
            "✅ Discovery flow found: {flow_id} with status={status}",
            flow_id=flow_id,
            status=discovery_flow.status,
        )
    )

    # Get master flow data for additional information
    master_flow = await get_master_flow(flow_id, db, context)
    phase_state = await build_phase_state(discovery_flow, master_flow)

    # Ensure all data is JSON serializable
    safe_metadata = safe_serialize(discovery_flow.metadata, "metadata")
    safe_phase_state = safe_serialize(phase_state, "phase_state")
    safe_phases_completed = safe_serialize(
        discovery_flow.phases_completed, "phases_completed"
    )

    # Load operational data
    raw_data = await load_raw_data(discovery_flow, db, flow_id)
    field_mappings = load_field_mappings(discovery_flow, flow_id)
    summary = build_summary(
        raw_data, discovery_flow, field_mappings, safe_phases_completed
    )

    # Extract additional data from master flow if available
    if master_flow:
        raw_data, summary = extract_master_flow_data(master_flow, raw_data, summary)

    return build_flow_status_response(
        flow_id,
        discovery_flow,
        safe_phase_state,
        safe_metadata,
        safe_phases_completed,
        raw_data,
        field_mappings,
        summary,
    )


async def update_flow_status(
    flow_id: str,
    status: str,
    db: AsyncSession,
    context: RequestContext,
    current_phase: str = None,
    error_message: str = None,
    metadata: Dict[str, Any] = None,
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
    # Import here to avoid circular imports
    from app.utils.flow_constants.flow_states import FlowPhase

    # Query for active flows with proper status AND phase filtering
    # Issue #128 fix: Include flows in early phases as active
    stmt = (
        select(DiscoveryFlow)
        .where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                # Status-based filtering (existing logic)
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

    # Also check for flows in early phases (Issue #128 fix)
    # These flows may have status != "initializing" but current_phase = "initialization"
    early_phase_stmt = (
        select(DiscoveryFlow)
        .where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.current_phase.in_(
                    [
                        FlowPhase.INITIALIZATION.value,
                        FlowPhase.DATA_IMPORT.value,
                        FlowPhase.DATA_VALIDATION.value,
                        FlowPhase.FIELD_MAPPING.value,
                        FlowPhase.DATA_CLEANSING.value,
                    ]
                ),
                # Exclude terminal states
                ~DiscoveryFlow.status.in_(
                    [
                        FlowStatus.COMPLETED.value,
                        FlowStatus.FAILED.value,
                        FlowStatus.CANCELLED.value,
                        FlowStatus.ARCHIVED.value,
                    ]
                ),
            )
        )
        .order_by(desc(DiscoveryFlow.updated_at))
        .limit(limit)
    )

    early_phase_result = await db.execute(early_phase_stmt)
    early_phase_flows = early_phase_result.scalars().all()

    # Merge the results and deduplicate
    all_flows = list(flows) + [f for f in early_phase_flows if f not in flows]

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

    # TODO: Performance Optimization - N+1 Query Issue
    # Current implementation calls check_actual_data_via_import_id() for each flow
    # Should batch query all import_ids upfront:
    #   1. Collect all import_ids: import_ids = [f.data_import_id for f in all_flows if f.data_import_id]
    #   2. Batch query import_field_mappings and data_imports tables with IN clause
    #   3. Build lookup dict: import_data_cache = {import_id: {...}}
    #   4. Use cache in loop below instead of individual queries
    # Estimated impact: 100 flows = 200 queries → 2 queries

    for flow in all_flows:
        if flow.flow_id not in flow_ids_seen:
            flow_ids_seen.add(flow.flow_id)

            # 🔧 FIX for Bug #560 (Progress Bar) & Bug #578 (Success Criteria)
            # Apply smart detection for data_import and field_mapping (same logic as FlowHandler)
            try:
                actual_data_status = (
                    await FlowHandlerHelpers.check_actual_data_via_import_id(flow)
                )
            except Exception as e:
                logger.warning(
                    f"Smart detection failed for flow {flow.flow_id}: {e}, using DB flags"
                )
                actual_data_status = {
                    "has_import_data": flow.data_import_completed,
                    "has_field_mappings": flow.field_mapping_completed,
                }

            # Use smart detection: check for actual data, fallback to DB flags
            phases_dict = {
                "data_import": actual_data_status.get(
                    "has_import_data", flow.data_import_completed
                ),
                "field_mapping": actual_data_status.get(
                    "has_field_mappings", flow.field_mapping_completed
                ),
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            # Calculate actual progress from detected phases
            # Bug #560: Fixed progress bar showing 0%
            # Bug #578: Fixed success criteria showing 0/6
            completed_phases = sum(
                [
                    phases_dict["data_import"],
                    phases_dict["field_mapping"],
                    phases_dict["data_cleansing"],
                    phases_dict["asset_inventory"],
                    phases_dict["dependency_analysis"],
                    phases_dict["tech_debt_assessment"],
                ]
            )
            actual_progress = round(
                (completed_phases / TOTAL_DISCOVERY_PHASES) * 100, 1
            )

            active_flows.append(
                {
                    "flow_id": flow.flow_id,
                    "flow_name": flow.flow_name,
                    "status": flow.status,
                    "current_phase": flow.current_phase,
                    "progress": actual_progress,  # Use calculated progress
                    "phases": phases_dict,  # Add phases for success criteria
                    "data_import_id": flow.data_import_id,  # Include data_import_id
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

            # Calculate progress from discovery flow if it exists (Issue #557 fix)
            progress = 0
            phases_dict = {}
            try:
                # Look up corresponding discovery flow to get completion flags
                discovery_flow_stmt = select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.master_flow_id == master_flow.flow_id,
                        DiscoveryFlow.client_account_id == context.client_account_id,
                        DiscoveryFlow.engagement_id == context.engagement_id,
                    )
                )
                discovery_result = await db.execute(discovery_flow_stmt)
                discovery_flow = discovery_result.scalar_one_or_none()

                if discovery_flow:
                    # 🔧 FIX for Bug #560 (Progress Bar) & Bug #578 (Success Criteria)
                    # Apply smart detection (same logic as FlowHandler)
                    try:
                        actual_data_status = (
                            await FlowHandlerHelpers.check_actual_data_via_import_id(
                                discovery_flow
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            f"Smart detection failed for flow {discovery_flow.flow_id}: {e}, using DB flags"
                        )
                        actual_data_status = {
                            "has_import_data": discovery_flow.data_import_completed,
                            "has_field_mappings": discovery_flow.field_mapping_completed,
                        }

                    # Build phases dict with smart detection
                    phases_dict = {
                        "data_import": actual_data_status.get(
                            "has_import_data", discovery_flow.data_import_completed
                        ),
                        "field_mapping": actual_data_status.get(
                            "has_field_mappings", discovery_flow.field_mapping_completed
                        ),
                        "data_cleansing": discovery_flow.data_cleansing_completed,
                        "asset_inventory": discovery_flow.asset_inventory_completed,
                        "dependency_analysis": discovery_flow.dependency_analysis_completed,
                        "tech_debt_assessment": discovery_flow.tech_debt_assessment_completed,
                    }

                    # Calculate from detected phases
                    # Bug #560: Fixed progress bar showing 0%
                    # Bug #578: Fixed success criteria showing 0/6
                    completed_phases = sum(
                        [
                            phases_dict["data_import"],
                            phases_dict["field_mapping"],
                            phases_dict["data_cleansing"],
                            phases_dict["asset_inventory"],
                            phases_dict["dependency_analysis"],
                            phases_dict["tech_debt_assessment"],
                        ]
                    )
                    progress = round(
                        (completed_phases / TOTAL_DISCOVERY_PHASES) * 100, 1
                    )
                else:
                    # Fallback to master flow's progress_percentage
                    progress = getattr(master_flow, "progress_percentage", 0) or 0
            except Exception as e:
                logger.warning(
                    f"Could not calculate progress for master flow {master_flow.flow_id}: {e}"
                )
                progress = getattr(master_flow, "progress_percentage", 0) or 0

            active_flows.append(
                {
                    "flow_id": master_flow.flow_id,
                    "flow_name": getattr(master_flow, "flow_name", "Unnamed Flow"),
                    "status": getattr(master_flow, "flow_status", "unknown"),
                    "current_phase": getattr(master_flow, "current_phase", None),
                    "progress": progress,  # Use calculated progress
                    "phases": phases_dict,  # Add phases for success criteria
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
