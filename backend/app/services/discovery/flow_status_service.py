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
from app.services.discovery.data_extraction_service import extract_raw_data

logger = logging.getLogger(__name__)


async def get_flow_status(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Dict[str, Any]:
    """Get the status of a discovery flow."""
    # Get the discovery flow
    discovery_flow = await _get_discovery_flow(flow_id, db, context)

    if discovery_flow:
        return await _process_found_flow(flow_id, discovery_flow, db, context)

    # Flow not found - perform debug check
    await _debug_flow_context(flow_id, db, context)


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
    master_flow = await _get_master_flow(flow_id, db, context)
    phase_state = await _build_phase_state(discovery_flow, master_flow)

    # Ensure all data is JSON serializable
    safe_metadata = _safe_serialize(discovery_flow.metadata, "metadata")
    safe_phase_state = _safe_serialize(phase_state, "phase_state")
    safe_phases_completed = _safe_serialize(
        discovery_flow.phases_completed, "phases_completed"
    )

    # Load operational data
    raw_data = await _load_raw_data(discovery_flow, db, flow_id)
    field_mappings = _load_field_mappings(discovery_flow, flow_id)
    summary = _build_summary(
        raw_data, discovery_flow, field_mappings, safe_phases_completed
    )

    # Extract additional data from master flow if available
    if master_flow:
        raw_data, summary = _extract_master_flow_data(master_flow, raw_data, summary)

    return _build_flow_status_response(
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


# Helper functions to reduce complexity


async def _get_discovery_flow(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Optional[DiscoveryFlow]:
    """Get discovery flow by ID and context"""
    stmt = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_master_flow(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> Optional[CrewAIFlowStateExtensions]:
    """Get master flow state data"""
    stmt = select(CrewAIFlowStateExtensions).where(
        and_(
            CrewAIFlowStateExtensions.flow_id == flow_id,
            CrewAIFlowStateExtensions.client_account_id == context.client_account_id,
            CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _build_phase_state(
    discovery_flow: DiscoveryFlow, master_flow: Optional[CrewAIFlowStateExtensions]
) -> Dict[str, Any]:
    """Build combined phase state from discovery and master flows"""
    phase_state = discovery_flow.phase_state or {}
    if master_flow and master_flow.flow_persistence_data:
        master_phase_state = master_flow.flow_persistence_data.get(
            "current_phase_state", {}
        )
        if master_phase_state:
            phase_state.update(master_phase_state)
    return phase_state


def _safe_serialize(data: Any, data_type: str) -> Dict[str, Any]:
    """Safely serialize data to avoid recursion errors"""
    if not data:
        return {}

    try:
        import json

        return json.loads(json.dumps(data))
    except (TypeError, ValueError, RecursionError):
        return {"error": f"{data_type}_serialization_failed"}


async def _load_raw_data(
    discovery_flow: DiscoveryFlow, db: AsyncSession, flow_id: str
) -> List[Dict[str, Any]]:
    """Load raw data from import records"""
    raw_data = []
    if discovery_flow.data_import_id:
        from app.models import RawImportRecord

        stmt = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == discovery_flow.data_import_id)
            .limit(1000)
        )
        result = await db.execute(stmt)
        import_records = result.scalars().all()

        for record in import_records:
            raw_data.append(
                {
                    "id": str(record.id) if hasattr(record, "id") else None,
                    "source": "data_import",
                    "data": record.raw_data if hasattr(record, "raw_data") else {},
                    "timestamp": (
                        record.created_at.isoformat()
                        if hasattr(record, "created_at")
                        else None
                    ),
                    "validation_status": "valid",
                }
            )

        logger.info(f"✅ Loaded {len(raw_data)} raw records for flow {flow_id}")

    return raw_data


def _load_field_mappings(discovery_flow: DiscoveryFlow, flow_id: str) -> Dict[str, Any]:
    """Load and parse field mappings from discovery flow"""
    field_mappings = {}
    if not discovery_flow.field_mappings:
        return field_mappings

    try:
        import json

        if isinstance(discovery_flow.field_mappings, str):
            field_mappings = json.loads(discovery_flow.field_mappings)
        elif isinstance(discovery_flow.field_mappings, dict):
            field_mappings = discovery_flow.field_mappings
        elif isinstance(discovery_flow.field_mappings, list):
            field_mappings = _convert_list_mappings_to_dict(
                discovery_flow.field_mappings
            )

        logger.info(
            f"✅ Loaded {len(field_mappings)} field mappings for flow {flow_id}"
        )
    except Exception as e:
        logger.error(f"Failed to parse field mappings: {e}")
        field_mappings = {}

    return field_mappings


def _convert_list_mappings_to_dict(
    mappings_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Convert list format mappings to dict format"""
    field_mappings = {}
    for mapping in mappings_list:
        if isinstance(mapping, dict) and "source_field" in mapping:
            field_mappings[mapping["source_field"]] = {
                "source_field": mapping.get("source_field"),
                "target_field": mapping.get("target_field"),
                "mapping_type": mapping.get("mapping_type", "direct"),
                "confidence": mapping.get("confidence", 1.0),
            }
    return field_mappings


def _build_summary(
    raw_data: List[Dict[str, Any]],
    discovery_flow: DiscoveryFlow,
    field_mappings: Dict[str, Any],
    safe_phases_completed: Dict[str, Any],
) -> Dict[str, Any]:
    """Build summary data for frontend compatibility"""
    return {
        "total_records": len(raw_data),
        "data_import_completed": bool(discovery_flow.data_import_id and raw_data),
        "field_mapping_completed": bool(field_mappings),
        "attribute_mapping_completed": bool(field_mappings),  # Alias for compatibility
        "data_cleansing_completed": (
            safe_phases_completed.get("data_cleansing", False)
            if safe_phases_completed
            else False
        ),
        "record_count": len(raw_data),
        "quality_score": 0,  # Would need to be calculated based on data quality metrics
    }


def _extract_master_flow_data(
    master_flow: CrewAIFlowStateExtensions,
    raw_data: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract additional data from master flow persistence data"""
    if not master_flow.flow_persistence_data:
        return raw_data, summary

    persistence_data = master_flow.flow_persistence_data
    if "crewai_state_data" in persistence_data:
        crewai_data = persistence_data["crewai_state_data"]
        extracted_raw = extract_raw_data(crewai_data)
        if extracted_raw and not raw_data:
            raw_data = extracted_raw
            summary["total_records"] = len(raw_data)
            logger.info(f"📦 Extracted {len(raw_data)} records from CrewAI state data")

    return raw_data, summary


def _build_flow_status_response(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    safe_phase_state: Dict[str, Any],
    safe_metadata: Dict[str, Any],
    safe_phases_completed: Dict[str, Any],
    raw_data: List[Dict[str, Any]],
    field_mappings: Dict[str, Any],
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the final flow status response"""
    return {
        "flow_id": flow_id,
        "status": discovery_flow.status,
        "current_phase": discovery_flow.current_phase,
        "progress": discovery_flow.progress_percentage or 0,
        "progress_percentage": discovery_flow.progress_percentage or 0,  # Alias
        "phase_state": safe_phase_state,
        "metadata": safe_metadata,
        "last_activity": (
            discovery_flow.updated_at.isoformat() if discovery_flow.updated_at else None
        ),
        "error_message": discovery_flow.error_message,
        "phase_completion": safe_phases_completed,
        "raw_data": raw_data,
        "field_mappings": field_mappings,
        "summary": summary,
        "data_import_id": discovery_flow.data_import_id,
        "import_metadata": {
            "record_count": len(raw_data),
            "import_id": discovery_flow.data_import_id,
        },
    }


async def _debug_flow_context(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> None:
    """Debug flow context when flow is not found"""
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
