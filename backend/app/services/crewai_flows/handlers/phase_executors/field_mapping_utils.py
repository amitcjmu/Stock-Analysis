"""
Field Mapping Executor Utilities

Utility functions and helpers for the field mapping executor.
Extracted from the main executor to maintain under 400 lines per file.

This module contains:
- Input validation utilities
- Execution context management
- Flow type support definitions
- CrewAI availability detection
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# CrewAI Flow availability detection for compatibility
CREWAI_FLOW_AVAILABLE = False
try:
    # CRITICAL FIX: Add concrete import to test availability
    from crewai import Flow
    from crewai.llm import LLM

    # Test that classes can be instantiated
    test_flow = Flow  # Just reference the class to ensure it's importable
    test_llm = LLM  # Just reference the class to ensure it's importable

    CREWAI_FLOW_AVAILABLE = True
    logger.info(
        "✅ CrewAI Flow and LLM imports available - concrete import test passed"
    )
except ImportError as e:
    CREWAI_FLOW_AVAILABLE = False
    logger.warning(f"CrewAI Flow not available: {e}")
except Exception as e:
    CREWAI_FLOW_AVAILABLE = False
    logger.warning(f"CrewAI imports failed: {e}")


def get_supported_flow_types() -> List[str]:
    """Return the flow types supported by the field mapping executor."""
    return ["unified_discovery", "field_mapping", "data_mapping"]


async def validate_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data for field mapping.

    Args:
        input_data: Dictionary containing input data to validate

    Returns:
        bool: True if input is valid, False otherwise

    Security:
        - Validates required fields to prevent execution with incomplete data
        - Checks for empty data structures that could cause processing errors
    """
    try:
        required_fields = ["sample_data", "detected_columns"]

        for field in required_fields:
            if field not in input_data:
                logger.warning(f"Missing required field: {field}")
                return False

        if not input_data.get("sample_data"):
            logger.warning("Empty sample_data provided")
            return False

        if not input_data.get("detected_columns"):
            logger.warning("Empty detected_columns provided")
            return False

        return True

    except Exception as e:
        logger.error(f"Input validation failed: {str(e)}")
        return False


def get_execution_context(
    phase_name: str, client_account_id: str, engagement_id: str, timeout: int
) -> Dict[str, Any]:
    """
    Get execution context for field mapping.

    Args:
        phase_name: Name of the current phase
        client_account_id: Client account identifier
        engagement_id: Engagement identifier
        timeout: Execution timeout in seconds

    Returns:
        Dict containing execution context information
    """
    return {
        "phase_name": phase_name,
        "client_account_id": client_account_id,
        "engagement_id": engagement_id,
        "timeout": timeout,
        "crewai_available": CREWAI_FLOW_AVAILABLE,
        "modular_implementation": True,
        "backward_compatible": True,
    }


def prepare_crew_input_from_state(state: Any) -> Dict[str, Any]:
    """
    Prepare input data for crew execution from state object.

    Args:
        state: State object containing discovery data

    Returns:
        Dict formatted for crew execution

    Security:
        - Provides safe defaults for missing data to prevent execution errors
        - Validates state object structure before accessing attributes
        - Ensures flow_id is converted to string for compatibility
    """
    try:
        # Extract data from the current state
        discovery_data = getattr(state, "discovery_data", {})
        field_mappings = getattr(state, "field_mappings", [])
        raw_data = getattr(state, "raw_data", [])

        # Get flow_id and ensure it's a string (not UUID object)
        flow_id = getattr(state, "flow_id", None)
        if flow_id and not isinstance(flow_id, str):
            flow_id = str(flow_id)

        crew_input = {
            "flow_id": flow_id,
            "discovery_data": discovery_data,
            "sample_data": discovery_data.get("sample_data", raw_data),
            "detected_columns": discovery_data.get("detected_columns", []),
            "data_source_info": discovery_data.get("data_source_info", {}),
            "previous_mappings": field_mappings,
            "mapping_type": "field_mapping",
        }

        logger.info(
            f"Prepared crew input with {len(crew_input.get('sample_data', []))} sample records"
        )
        return crew_input

    except Exception as e:
        logger.error(f"Failed to prepare crew input: {str(e)}")
        # Return minimal valid input with flow_id as string
        flow_id = getattr(state, "flow_id", "unknown")
        if flow_id and not isinstance(flow_id, str):
            flow_id = str(flow_id)

        return {
            "flow_id": flow_id,
            "discovery_data": {},
            "sample_data": [],
            "detected_columns": [],
            "data_source_info": {},
            "previous_mappings": [],
            "mapping_type": "field_mapping",
        }


def store_results_in_state(state: Any, results: Dict[str, Any]) -> None:
    """
    Store execution results in state object.

    Args:
        state: State object to update
        results: Results dictionary from execution

    Security:
        - Safely handles missing state attributes
        - Logs validation errors without breaking flow
        - Preserves existing state structure
    """
    try:
        logger.info(f"Storing field mapping results with keys: {list(results.keys())}")

        # Store mappings in state
        if "mappings" in results:
            state.field_mappings = results["mappings"]
            logger.info(f"Stored {len(results['mappings'])} field mappings")

        # Store confidence scores
        if "confidence_scores" in results:
            if not hasattr(state, "field_mapping_metadata"):
                state.field_mapping_metadata = {}
            state.field_mapping_metadata["confidence_scores"] = results[
                "confidence_scores"
            ]

        # Store clarifications
        if "clarifications" in results:
            if not hasattr(state, "field_mapping_metadata"):
                state.field_mapping_metadata = {}
            state.field_mapping_metadata["clarifications"] = results["clarifications"]

        # Store validation errors if any
        if "validation_errors" in results and results["validation_errors"]:
            logger.warning(
                f"Field mapping validation errors: {results['validation_errors']}"
            )
            if not hasattr(state, "validation_errors"):
                state.validation_errors = []
            state.validation_errors.extend(results["validation_errors"])

        # Store execution metadata
        if "execution_metadata" in results:
            if not hasattr(state, "field_mapping_metadata"):
                state.field_mapping_metadata = {}
            state.field_mapping_metadata.update(results["execution_metadata"])

        logger.info("Field mapping results stored successfully in state")

    except Exception as e:
        logger.error(f"Failed to store field mapping results: {str(e)}")
        # Don't raise exception to avoid breaking the flow
        # Just log the error and continue
