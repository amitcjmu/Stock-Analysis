"""Schema validation for gap enhancement outputs.

Provides strict validation of AI agent outputs with:
- Required field checks
- Type validation (confidence_score, ai_suggestions)
- Gap count verification
- Structured error codes
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def validate_enhancement_output(  # noqa: C901
    result: Dict[str, Any], input_gaps: List[Dict]
) -> List[str]:
    """Validate enhancement output against strict schema.

    Args:
        result: Parsed output from agent (from parse_task_output)
        input_gaps: Original input gaps (for count verification)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check top-level structure
    if "gaps" not in result:
        errors.append("Missing 'gaps' key in output")
        return errors  # Can't continue without gaps key

    gaps = result["gaps"]

    # Check priority keys
    for priority in ["critical", "high", "medium", "low"]:
        if priority not in gaps:
            errors.append(f"Missing '{priority}' priority in gaps")
        elif not isinstance(gaps[priority], list):
            errors.append(
                f"'{priority}' must be a list, got {type(gaps[priority]).__name__}"
            )

    # Validate each gap
    input_gap_ids = {(g.get("asset_id"), g.get("field_name")) for g in input_gaps}
    output_gap_count = 0
    output_gap_ids = set()

    for priority, gap_list in gaps.items():
        if not isinstance(gap_list, list):
            continue  # Already reported above

        for idx, gap in enumerate(gap_list):
            output_gap_count += 1

            # Required fields
            required = ["asset_id", "field_name", "gap_type", "priority"]
            for field in required:
                if field not in gap:
                    errors.append(
                        f"{priority}[{idx}]: Missing required field '{field}'"
                    )

            # Track output gap IDs for comparison
            if "asset_id" in gap and "field_name" in gap:
                output_gap_ids.add((gap["asset_id"], gap["field_name"]))

            # Validate confidence_score (if present)
            if "confidence_score" in gap:
                score = gap["confidence_score"]
                if not isinstance(score, (int, float)):
                    errors.append(
                        f"{priority}[{idx}]: confidence_score must be numeric, "
                        f"got {type(score).__name__}"
                    )
                elif isinstance(score, (int, float)):
                    # Check for NaN/Inf
                    import math

                    if math.isnan(score) or math.isinf(score):
                        errors.append(
                            f"{priority}[{idx}]: confidence_score cannot be NaN or Inf"
                        )
                    elif not (0.0 <= score <= 1.0):
                        errors.append(
                            f"{priority}[{idx}]: confidence_score must be 0.0-1.0, "
                            f"got {score}"
                        )

            # Validate ai_suggestions (if present)
            if "ai_suggestions" in gap:
                suggestions = gap["ai_suggestions"]
                if not isinstance(suggestions, list):
                    errors.append(
                        f"{priority}[{idx}]: ai_suggestions must be a list, "
                        f"got {type(suggestions).__name__}"
                    )
                elif len(suggestions) == 0:
                    errors.append(f"{priority}[{idx}]: ai_suggestions cannot be empty")
                else:
                    # Validate each suggestion is a string
                    for s_idx, suggestion in enumerate(suggestions):
                        if not isinstance(suggestion, str):
                            errors.append(
                                f"{priority}[{idx}].ai_suggestions[{s_idx}]: "
                                f"must be string, got {type(suggestion).__name__}"
                            )

            # Validate suggested_resolution (if present)
            if "suggested_resolution" in gap:
                resolution = gap["suggested_resolution"]
                if not isinstance(resolution, str):
                    errors.append(
                        f"{priority}[{idx}]: suggested_resolution must be string, "
                        f"got {type(resolution).__name__}"
                    )
                elif len(resolution.strip()) == 0:
                    errors.append(
                        f"{priority}[{idx}]: suggested_resolution cannot be empty"
                    )

    # Check gap count
    if output_gap_count != len(input_gaps):
        errors.append(
            f"Gap count mismatch: expected {len(input_gaps)}, got {output_gap_count}"
        )

    # Check for missing gaps (gaps in input but not in output)
    missing_gaps = input_gap_ids - output_gap_ids
    if missing_gaps:
        errors.append(
            f"Missing gaps in output: {len(missing_gaps)} gaps from input not found in output"
        )

    # Check for extra gaps (gaps in output but not in input)
    extra_gaps = output_gap_ids - input_gap_ids
    if extra_gaps:
        errors.append(
            f"Extra gaps in output: {len(extra_gaps)} gaps in output not present in input"
        )

    return errors


def sanitize_numeric_fields(gaps: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Sanitize numeric fields (remove NaN/Inf, clamp to valid ranges).

    Args:
        gaps: Gap dict with priority keys

    Returns:
        Sanitized gaps dict (mutates in place, also returns for convenience)
    """
    import math

    for priority, gap_list in gaps.items():
        for gap in gap_list:
            # Sanitize confidence_score
            if "confidence_score" in gap:
                score = gap["confidence_score"]
                if isinstance(score, (int, float)):
                    # Remove NaN/Inf
                    if math.isnan(score) or math.isinf(score):
                        logger.warning(
                            f"Removed invalid confidence_score (NaN/Inf) for "
                            f"{gap.get('asset_id')}:{gap.get('field_name')}"
                        )
                        gap["confidence_score"] = None
                    # Clamp to 0.0-1.0
                    elif score < 0.0:
                        gap["confidence_score"] = 0.0
                    elif score > 1.0:
                        gap["confidence_score"] = 1.0
                else:
                    # Non-numeric, set to None
                    gap["confidence_score"] = None

    return gaps
