"""Output parsing utilities for gap analysis."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_task_output(task_output: Any) -> Dict[str, Any]:  # noqa: C901
    """Parse task output with proper error handling.

    Args:
        task_output: Raw task output from CrewAI agent

    Returns:
        Parsed dict with gaps, questionnaire, and summary
    """
    raw_output = task_output.raw if hasattr(task_output, "raw") else str(task_output)

    try:
        # Try to parse as JSON
        result = json.loads(raw_output)

        # Ensure required structure exists
        if "gaps" not in result:
            result["gaps"] = {}
        if "questionnaire" not in result:
            result["questionnaire"] = {"sections": []}
        if "summary" not in result:
            result["summary"] = {
                "total_gaps": 0,
                "assets_analyzed": 0,
            }

        return result

    except json.JSONDecodeError:
        logger.warning("Task output not valid JSON, attempting to extract data")

        # Try to find ALL JSON blocks within the text (handles multi-task agent output)
        json_candidates = []
        idx = 0
        while idx < len(raw_output):
            start = raw_output.find("{", idx)
            if start == -1:
                break

            # Find matching closing brace
            depth = 0
            end = start
            for i in range(start, len(raw_output)):
                if raw_output[i] == "{":
                    depth += 1
                elif raw_output[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break

            if end > start:
                try:
                    potential_json = raw_output[start : end + 1]
                    parsed = json.loads(potential_json)
                    json_candidates.append(parsed)
                    logger.debug(f"Found JSON candidate: {list(parsed.keys())}")
                except json.JSONDecodeError:
                    pass

            idx = end + 1 if end > start else start + 1

        # Prioritize JSON blocks that have "gaps" key with data
        for candidate in json_candidates:
            if "gaps" in candidate and candidate["gaps"]:
                # Count total gaps
                gap_count = sum(
                    len(v) if isinstance(v, list) else 0
                    for v in candidate["gaps"].values()
                )
                if gap_count > 0:
                    logger.info(
                        f"Selected JSON with {gap_count} gaps from {len(json_candidates)} candidates"
                    )
                    # Ensure required structure exists
                    if "questionnaire" not in candidate:
                        candidate["questionnaire"] = {"sections": []}
                    if "summary" not in candidate:
                        candidate["summary"] = {
                            "total_gaps": gap_count,
                            "assets_analyzed": 0,
                        }
                    return candidate

        # If no gaps found, try any JSON with "gaps" key
        for candidate in json_candidates:
            if "gaps" in candidate:
                logger.warning("Selected JSON with empty gaps")
                if "questionnaire" not in candidate:
                    candidate["questionnaire"] = {"sections": []}
                if "summary" not in candidate:
                    candidate["summary"] = {"total_gaps": 0, "assets_analyzed": 0}
                return candidate

        logger.warning(
            f"No valid JSON with gaps found among {len(json_candidates)} candidates"
        )

        # Return minimal structure with raw output
        return {
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0},
            "raw_output": raw_output,
        }
