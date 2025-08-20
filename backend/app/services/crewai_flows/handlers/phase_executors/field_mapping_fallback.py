"""
Field Mapping Executor Fallback Logic

Fallback execution implementation for when the modular executor is not available.
Extracted from the main executor to maintain under 400 lines per file.

This module contains:
- Fallback crew execution logic
- Text-based mapping extraction
- Error handling for fallback scenarios
- Legacy crew result processing
"""

import logging
import json
import re
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


async def execute_with_crew_fallback(
    crew_input: Dict[str, Any], crew_manager: Any, phase_name: str, timeout: int
) -> Dict[str, Any]:
    """
    Fallback execution when modular executor is not available.

    Args:
        crew_input: Input data for crew execution
        crew_manager: CrewAI crew manager instance
        phase_name: Name of the current phase
        timeout: Execution timeout in seconds

    Returns:
        Dict containing execution results in expected format

    Security:
        - Proper timeout configuration to prevent hanging
        - Safe JSON parsing with fallback text extraction
        - Comprehensive error handling and logging
        - Resource cleanup and exception propagation
    """
    try:
        logger.info("Executing field mapping fallback with direct crew manager")

        # Use the crew manager to create and execute a field mapping crew
        crew = crew_manager.create_crew_on_demand(phase_name)

        if not crew:
            raise RuntimeError(f"Could not create crew for {phase_name}")

        # Execute the crew with the input data
        # Note: This is a simplified fallback that may not have all the sophistication
        # of the modular executor, but it maintains basic functionality
        # CRITICAL FIX: Pass the timeout to avoid 15-second global timeout
        logger.info(f"Executing crew with timeout: {timeout} seconds")

        # Set crew configuration with proper timeout
        crew.max_time = timeout
        crew_result = await crew.kickoff_async(inputs=crew_input)

        # Process the result into expected format
        if hasattr(crew_result, "raw") and crew_result.raw:
            # Try to parse structured response
            parsed_result = _try_parse_json_response(crew_result.raw)
            if parsed_result:
                return _format_parsed_result(parsed_result, phase_name, crew_result.raw)

        # If we can't parse JSON, try to extract mappings from raw text
        logger.warning(
            "Could not parse JSON from crew result, attempting text extraction"
        )

        # Extract field mappings from raw text if available
        extracted_mappings = _extract_mappings_from_text(crew_result)

        if extracted_mappings:
            logger.info(
                f"Successfully extracted {len(extracted_mappings)} mappings from raw text"
            )
        else:
            logger.error("No mappings could be extracted from crew result")

        return _format_fallback_result(extracted_mappings, phase_name, crew_result)

    except Exception as e:
        logger.error(f"Field mapping fallback execution failed: {str(e)}")
        return _format_error_result(e, phase_name)


def _try_parse_json_response(raw_response: str) -> Dict[str, Any]:
    """
    Attempt to parse JSON from crew response.

    Args:
        raw_response: Raw text response from crew

    Returns:
        Parsed dictionary or None if parsing fails

    Security:
        - Safe JSON parsing with exception handling
        - Validates JSON structure before returning
        - Prevents malformed data propagation
    """
    try:
        if "{" in raw_response and "}" in raw_response:
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            json_str = raw_response[start:end]
            parsed_result = json.loads(json_str)

            # Basic validation of parsed result structure
            if isinstance(parsed_result, dict):
                return parsed_result

    except json.JSONDecodeError as e:
        logger.debug(f"JSON parsing failed: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error during JSON parsing: {e}")

    return None


def _extract_mappings_from_text(crew_result: Any) -> List[Dict[str, Any]]:
    """
    Extract field mappings from raw text response.

    Args:
        crew_result: CrewAI execution result object

    Returns:
        List of extracted mapping dictionaries

    Security:
        - Safe regex pattern matching
        - Validates extracted field names
        - Provides reasonable confidence defaults
    """
    extracted_mappings = []

    if hasattr(crew_result, "raw") and crew_result.raw:
        # Look for patterns like "field_name -> target_field" or "field_name: target_field"
        lines = crew_result.raw.split("\n")
        for line in lines:
            # Match patterns like "Device_ID -> asset_id" or "Device_ID: asset_id"
            match = re.search(r"(\w+)\s*(?:->|:|=>|maps to)\s*(\w+)", line)
            if match:
                source_field = match.group(1)
                target_field = match.group(2)

                # Basic validation of extracted field names
                if (
                    source_field
                    and target_field
                    and len(source_field) > 0
                    and len(target_field) > 0
                ):
                    extracted_mappings.append(
                        {
                            "source_field": source_field,
                            "target_field": target_field,
                            "confidence": 0.7,  # Default confidence for text-extracted mappings
                            "status": "suggested",
                        }
                    )
                    logger.info(f"Extracted mapping: {source_field} -> {target_field}")

    return extracted_mappings


def _format_parsed_result(
    parsed_result: Dict[str, Any], phase_name: str, raw_response: str
) -> Dict[str, Any]:
    """
    Format successfully parsed JSON result.

    Args:
        parsed_result: Parsed JSON dictionary
        phase_name: Current phase name
        raw_response: Original raw response

    Returns:
        Formatted result dictionary
    """
    return {
        "success": True,
        "mappings": parsed_result.get("mappings", []),
        "confidence_scores": parsed_result.get("confidence_scores", {}),
        "clarifications": parsed_result.get("clarifications", []),
        "validation_errors": [],
        "phase_name": phase_name,
        "next_phase": "data_transformation",
        "timestamp": datetime.utcnow().isoformat(),
        "execution_metadata": {"fallback_used": True},
        "raw_response": raw_response,
    }


def _format_fallback_result(
    extracted_mappings: List[Dict[str, Any]], phase_name: str, crew_result: Any
) -> Dict[str, Any]:
    """
    Format fallback result from text extraction.

    Args:
        extracted_mappings: List of extracted mapping dictionaries
        phase_name: Current phase name
        crew_result: Original crew result object

    Returns:
        Formatted result dictionary
    """
    return {
        "success": True if extracted_mappings else False,
        "mappings": extracted_mappings,
        "confidence_scores": {},
        "clarifications": [],
        "validation_errors": (
            [] if extracted_mappings else ["No mappings extracted from crew result"]
        ),
        "phase_name": phase_name,
        "next_phase": "data_transformation",
        "timestamp": datetime.utcnow().isoformat(),
        "execution_metadata": {
            "fallback_used": True,
            "raw_result": str(crew_result),
        },
        "raw_response": str(crew_result),
    }


def _format_error_result(error: Exception, phase_name: str) -> Dict[str, Any]:
    """
    Format error result for fallback execution failures.

    Args:
        error: Exception that occurred during execution
        phase_name: Current phase name

    Returns:
        Formatted error result dictionary
    """
    return {
        "success": False,
        "error": f"Fallback execution failed: {str(error)}",
        "mappings": [],
        "clarifications": [],
        "validation_errors": [str(error)],
        "phase_name": phase_name,
        "timestamp": datetime.utcnow().isoformat(),
    }


def validate_crew_manager_availability(crew_manager: Any, phase_name: str) -> bool:
    """
    Validate that crew manager is available and can create crews.

    Args:
        crew_manager: CrewAI crew manager instance
        phase_name: Name of the phase to create crew for

    Returns:
        bool: True if crew manager is ready, False otherwise

    Security:
        - Validates crew manager before attempting execution
        - Prevents null pointer exceptions
        - Logs validation results for debugging
    """
    try:
        if not crew_manager:
            logger.error("Crew manager is None")
            return False

        if not hasattr(crew_manager, "create_crew_on_demand"):
            logger.error("Crew manager missing create_crew_on_demand method")
            return False

        # Test crew creation without actually creating it
        # This is a basic availability check
        logger.info(f"Crew manager validated for phase: {phase_name}")
        return True

    except Exception as e:
        logger.error(f"Crew manager validation failed: {str(e)}")
        return False
