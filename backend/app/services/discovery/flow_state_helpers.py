"""
Helper functions for flow state loading and preparation.

Extracted from flow_execution_service.py to reduce complexity and file length.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flows.flow_state_manager import FlowStateManager

logger = logging.getLogger(__name__)


async def load_flow_state_for_phase(
    db: AsyncSession, context: RequestContext, flow_id: str, phase_name: str
) -> Dict[str, Any]:
    """
    Load flow state data for a specific phase execution.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        phase_name: Name of the phase to execute

    Returns:
        Phase input dictionary with flow state data
    """
    try:
        # Initialize flow state manager
        state_manager = FlowStateManager(db, context)

        # Load the flow state
        flow_state = await state_manager.get_flow_state(flow_id)

        if not flow_state:
            logger.warning(f"No flow state found for {flow_id}, using empty state")
            flow_state = UnifiedDiscoveryFlowState(flow_id=flow_id)

        # Convert to dict if it's a Pydantic model
        if hasattr(flow_state, "model_dump"):
            flow_state_dict = flow_state.model_dump()
        elif hasattr(flow_state, "dict"):
            flow_state_dict = flow_state.dict()
        else:
            flow_state_dict = dict(flow_state) if flow_state else {}

        # CRITICAL FIX: Get data_import_id from discovery flow for asset_inventory phase
        data_import_id = None
        master_flow_id = None
        if phase_name == "asset_inventory":
            from sqlalchemy import select
            from app.models.discovery_flow import DiscoveryFlow

            # Get data_import_id from discovery flow record
            discovery_result = await db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            )
            discovery_flow = discovery_result.scalar_one_or_none()

            if discovery_flow:
                data_import_id = discovery_flow.data_import_id
                master_flow_id = discovery_flow.master_flow_id
                logger.info(
                    f"📦 Found data_import_id={data_import_id} for asset_inventory phase"
                )
            else:
                logger.warning(
                    f"No discovery flow found for {flow_id}, data_import_id will be None"
                )

        # Prepare phase-specific input based on phase name
        phase_input = prepare_phase_input(
            flow_state_dict, phase_name, flow_id, data_import_id, master_flow_id
        )

        raw_count = (
            len(phase_input.get("raw_data", []))
            if isinstance(phase_input.get("raw_data"), list)
            else 0
        )
        processed_count = (
            len(phase_input.get("processed_data", []))
            if isinstance(phase_input.get("processed_data"), list)
            else 0
        )
        logger.info(
            f"Loaded flow state for {phase_name} phase: "
            f"{raw_count} raw records, {processed_count} processed records"
        )

        return phase_input

    except Exception as e:
        logger.error(f"Error loading flow state for phase {phase_name}: {e}")
        # Return minimal phase input on error
        return {"flow_id": flow_id, "phase": phase_name, "error": str(e)}


def prepare_phase_input(
    flow_state_dict: Dict[str, Any],
    phase_name: str,
    flow_id: str,
    data_import_id: str = None,
    master_flow_id: str = None,
) -> Dict[str, Any]:
    """
    Prepare phase-specific input based on flow state and phase requirements.

    Args:
        flow_state_dict: Flow state as dictionary
        phase_name: Name of the phase
        flow_id: Flow identifier
        data_import_id: Data import ID (required for asset_inventory phase)
        master_flow_id: Master flow ID

    Returns:
        Phase input dictionary
    """
    # Base phase input
    phase_input = {"flow_id": flow_id, "phase": phase_name}

    # Add data_import_id if provided (critical for asset_inventory phase)
    if data_import_id:
        phase_input["data_import_id"] = data_import_id

    # Add master_flow_id if provided
    if master_flow_id:
        phase_input["master_flow_id"] = master_flow_id

    # Add phase-specific data based on phase requirements
    if phase_name == "asset_inventory":
        # Asset inventory needs raw data and processed data
        phase_input.update(
            {
                "raw_data": flow_state_dict.get("raw_data", []),
                "processed_data": flow_state_dict.get("processed_data", []),
                "cleaned_data": flow_state_dict.get(
                    "processed_data", []
                ),  # Use processed as cleaned if not available
                "field_mappings": flow_state_dict.get("field_mappings", {}),
                "approved_mappings": flow_state_dict.get("approved_mappings", {}),
                "confidence_score": flow_state_dict.get("confidence_score", 0),
            }
        )
    elif phase_name == "dependency_analysis":
        # Dependency analysis needs asset inventory data
        phase_input.update(
            {
                "asset_inventory": flow_state_dict.get("asset_inventory", {}),
                "processed_data": flow_state_dict.get("processed_data", []),
                "field_mappings": flow_state_dict.get("field_mappings", {}),
            }
        )
    elif phase_name == "critical_attributes":
        # Critical attributes needs processed data and mappings
        phase_input.update(
            {
                "processed_data": flow_state_dict.get("processed_data", []),
                "field_mappings": flow_state_dict.get("field_mappings", {}),
                "critical_attributes_assessment": flow_state_dict.get(
                    "critical_attributes_assessment", {}
                ),
            }
        )
    elif phase_name == "field_mapping":
        # Field mapping needs raw data
        phase_input.update(
            {
                "raw_data": flow_state_dict.get("raw_data", []),
                "user_headers": flow_state_dict.get("user_headers", []),
                "sample_data": flow_state_dict.get("sample_data", []),
            }
        )
    elif phase_name == "data_cleansing":
        # Data cleansing needs raw data and mappings
        phase_input.update(
            {
                "raw_data": flow_state_dict.get("raw_data", []),
                "field_mappings": flow_state_dict.get("field_mappings", {}),
                "approved_mappings": flow_state_dict.get("approved_mappings", {}),
            }
        )
    else:
        # Default: include all potentially relevant data
        phase_input.update(
            {
                "raw_data": flow_state_dict.get("raw_data", []),
                "processed_data": flow_state_dict.get("processed_data", []),
                "field_mappings": flow_state_dict.get("field_mappings", {}),
            }
        )

    return phase_input
