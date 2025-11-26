"""
Result parsing utilities for Cost Estimation Service.

This module handles parsing and validation of cost estimation results
from CrewAI agents, implementing safe JSON parsing per ADR-029.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_cost_result(
    result: Any, default_rate_cards: Dict[str, float]
) -> Dict[str, Any]:
    """
    Parse cost estimation result from agent using safe JSON parsing (ADR-029).

    Args:
        result: Raw result from CrewAI task
        default_rate_cards: Default rate cards for metadata

    Returns:
        Parsed cost estimation data dict
    """
    raw_output = result.raw if hasattr(result, "raw") else str(result)

    try:
        # Try direct JSON parse first
        cost_data = json.loads(raw_output)
    except json.JSONDecodeError:
        logger.warning("Cost result not valid JSON, extracting JSON blocks")
        cost_data = _extract_json_from_output(raw_output)

    # Ensure required structure
    cost_data = _ensure_required_structure(cost_data)

    # Add metadata
    cost_data["metadata"] = {
        "generated_by": "cost_estimation_specialist",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent_type": "crewai",
        "rate_cards_used": default_rate_cards,
    }

    return cost_data


def _extract_json_from_output(raw_output: str) -> Dict[str, Any]:
    """
    Extract JSON blocks from raw output using brace matching.

    Args:
        raw_output: Raw string output from agent

    Returns:
        Extracted JSON data or fallback structure
    """
    json_candidates = _find_json_candidates(raw_output)

    # Prioritize largest valid JSON with required structure
    for candidate in sorted(json_candidates, key=lambda x: x["size"], reverse=True):
        data = candidate["data"]
        if _has_cost_structure(data):
            logger.info(f"✅ Extracted cost JSON (size={candidate['size']})")
            return data

    # No valid cost JSON found
    logger.warning("No valid cost JSON found, using fallback")
    return _create_fallback_structure()


def _find_json_candidates(raw_output: str) -> List[Dict[str, Any]]:
    """
    Find all potential JSON objects in raw output.

    Args:
        raw_output: Raw string to search

    Returns:
        List of candidate JSON objects with metadata
    """
    json_candidates = []
    idx = 0
    while idx < len(raw_output):
        start = raw_output.find("{", idx)
        if start == -1:
            break

        # Find matching closing brace
        end = _find_matching_brace(raw_output, start)

        if end > start:
            candidate = _try_parse_json_candidate(raw_output, start, end)
            if candidate:
                json_candidates.append(candidate)

        idx = end + 1 if end > start else start + 1

    return json_candidates


def _find_matching_brace(text: str, start_pos: int) -> int:
    """
    Find the matching closing brace for an opening brace.

    Args:
        text: Text to search
        start_pos: Position of opening brace

    Returns:
        Position of matching closing brace, or -1 if not found
    """
    depth = 0
    for i in range(start_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _try_parse_json_candidate(
    raw_output: str, start: int, end: int
) -> Dict[str, Any] | None:
    """
    Attempt to parse a JSON candidate from raw output.

    Args:
        raw_output: Raw output string
        start: Start position
        end: End position

    Returns:
        Candidate dict with data and metadata, or None if parse fails
    """
    try:
        potential_json = raw_output[start : end + 1]
        parsed = json.loads(potential_json)
        return {"data": parsed, "size": end - start, "start_pos": start}
    except json.JSONDecodeError:
        return None


def _has_cost_structure(data: Dict[str, Any]) -> bool:
    """
    Check if data has required cost estimation structure.

    Args:
        data: Data dict to check

    Returns:
        True if has cost structure, False otherwise
    """
    return "labor_costs" in data or "total_cost" in data or "cost_breakdown" in data


def _create_fallback_structure() -> Dict[str, Any]:
    """
    Create fallback cost structure when parsing fails.

    Returns:
        Fallback cost data dict
    """
    return {
        "labor_costs": {},
        "infrastructure_costs": {},
        "total_cost": 0.0,
        "parsing_error": "Failed to extract valid cost data from agent output",
    }


def _ensure_required_structure(cost_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure cost data has all required fields.

    Args:
        cost_data: Cost data to validate

    Returns:
        Cost data with all required fields
    """
    if "labor_costs" not in cost_data:
        cost_data["labor_costs"] = {}
    if "infrastructure_costs" not in cost_data:
        cost_data["infrastructure_costs"] = {}
    if "total_cost" not in cost_data:
        cost_data["total_cost"] = 0.0
    if "confidence_intervals" not in cost_data:
        cost_data["confidence_intervals"] = {
            "low": 0.0,
            "medium": 0.0,
            "high": 0.0,
        }

    return cost_data
