"""Output parsing utilities for gap analysis."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_task_output(task_output: Any) -> Dict[str, Any]:
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

        # Try to find a JSON block within the text
        try:
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                potential_json = raw_output[start : end + 1]
                return json.loads(potential_json)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted JSON-like content.")

        # Return minimal structure with raw output
        return {
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0},
            "raw_output": raw_output,
        }
