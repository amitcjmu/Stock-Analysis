"""Output parsing utilities for gap analysis."""

import json
import logging
import re
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

        # Try to find JSON in the text
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return minimal structure with raw output
        return {
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0},
            "raw_output": raw_output,
        }
