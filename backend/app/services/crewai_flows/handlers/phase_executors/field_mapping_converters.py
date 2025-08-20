"""
Field Mapping Executor Converters

Conversion methods between different data formats for field mapping executor.
Extracted from the main executor to maintain under 400 lines per file.

This module contains:
- Crew input to state conversion
- Result to crew format conversion
- Data format transformation utilities
"""

import logging
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def convert_crew_input_to_state(crew_input: Dict[str, Any], state: Any) -> Any:
    """
    Convert legacy crew_input format to UnifiedDiscoveryFlowState.

    Args:
        crew_input: Dictionary containing crew execution input
        state: Original state object for context extraction

    Returns:
        UnifiedDiscoveryFlowState object compatible with modular executor

    Security:
        - Validates required fields with safe defaults
        - Ensures discovery_data structure integrity
        - Prevents null/undefined field access
    """
    from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

    # Extract data from crew_input
    engagement_id = getattr(state, "engagement_id", "unknown")
    client_account_id = getattr(state, "client_account_id", "unknown")
    flow_id = crew_input.get("flow_id", f"compat_{engagement_id}")
    discovery_data = crew_input.get("discovery_data", {})

    # Ensure discovery_data has required fields
    if "sample_data" not in discovery_data:
        discovery_data["sample_data"] = crew_input.get("sample_data", [])
    if "detected_columns" not in discovery_data:
        discovery_data["detected_columns"] = crew_input.get("detected_columns", [])
    if "data_source_info" not in discovery_data:
        discovery_data["data_source_info"] = crew_input.get("data_source_info", {})

    # Create state object
    mock_state = UnifiedDiscoveryFlowState(
        flow_id=flow_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_type="unified_discovery",
        current_phase="field_mapping",
        discovery_data=discovery_data,
        field_mappings=crew_input.get("previous_mappings", []),
    )

    logger.info(
        f"Converted crew input to state for engagement {engagement_id} with "
        f"{len(discovery_data.get('sample_data', []))} sample records"
    )

    return mock_state


def convert_result_to_crew_format(
    result: Dict[str, Any], phase_name: str
) -> Dict[str, Any]:
    """
    Convert modular execution result to legacy crew format.

    Args:
        result: Result dictionary from modular executor
        phase_name: Name of the current phase

    Returns:
        Dict formatted for crew execution compatibility

    Security:
        - Provides safe defaults for missing result fields
        - Ensures consistent return format structure
        - Preserves error information for debugging
    """
    crew_result = {
        "success": result.get("success", True),
        "mappings": result.get("mappings", []),
        "confidence_scores": result.get("confidence_scores", {}),
        "clarifications": result.get("clarifications", []),
        "validation_errors": result.get("validation_errors", []),
        "phase_name": phase_name,
        "next_phase": result.get("next_phase", "data_transformation"),
        "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
        "execution_metadata": result.get("execution_metadata", {}),
        "raw_response": result.get("raw_response", ""),
    }

    logger.info(
        f"Converted modular result to crew format with "
        f"{len(crew_result['mappings'])} mappings, "
        f"success: {crew_result['success']}"
    )

    return crew_result


def extract_data_from_crew_input_for_fallback(
    crew_input: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract and format data from crew_input for fallback execution.

    Args:
        crew_input: Original crew input dictionary

    Returns:
        Dict containing extracted data for fallback processing
    """
    return {
        "flow_id": crew_input.get("flow_id", "unknown"),
        "discovery_data": crew_input.get("discovery_data", {}),
        "sample_data": crew_input.get("sample_data", []),
        "detected_columns": crew_input.get("detected_columns", []),
        "data_source_info": crew_input.get("data_source_info", {}),
        "previous_mappings": crew_input.get("previous_mappings", []),
    }


def convert_flow_state_to_crew_input(flow_state: Any) -> Dict[str, Any]:
    """
    Convert flow state object to crew_input format for fallback execution.

    Args:
        flow_state: UnifiedDiscoveryFlowState or similar state object

    Returns:
        Dict formatted for crew execution

    Security:
        - Safely extracts nested data with defaults
        - Handles missing attributes gracefully
        - Validates data structure before access
    """
    try:
        discovery_data = getattr(flow_state, "discovery_data", {})

        crew_input = {
            "flow_id": getattr(flow_state, "flow_id", "unknown"),
            "discovery_data": discovery_data,
            "sample_data": discovery_data.get("sample_data", []),
            "detected_columns": discovery_data.get("detected_columns", []),
            "data_source_info": discovery_data.get("data_source_info", {}),
            "previous_mappings": getattr(flow_state, "field_mappings", []),
        }

        logger.info(
            f"Converted flow state to crew input for flow {crew_input['flow_id']}"
        )

        return crew_input

    except Exception as e:
        logger.error(f"Failed to convert flow state to crew input: {str(e)}")
        # Return minimal valid structure
        return {
            "flow_id": "unknown",
            "discovery_data": {},
            "sample_data": [],
            "detected_columns": [],
            "data_source_info": {},
            "previous_mappings": [],
        }
