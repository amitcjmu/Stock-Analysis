"""
Utility functions for extracting data from execution results.

Contains helper functions for extracting agent insights and phase data
from CrewAI execution results.
"""

from typing import Any, Dict, List, Optional


def extract_agent_insights(result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract agent insights from execution result.

    Args:
        result: Execution result dictionary

    Returns:
        List of agent insight dictionaries
    """
    agent_insights = []

    # Check for direct agent_insights in phase data
    phase_data = result.get("result", {}).get("crew_results", {}) or {}
    if "agent_insights" in phase_data:
        agent_insights = phase_data["agent_insights"]
    elif "crew_results" in result.get("result", {}) and isinstance(
        result["result"]["crew_results"], dict
    ):
        crew_results = result["result"]["crew_results"]
        if "message" in crew_results:
            agent_insights = [
                {"type": "completion", "content": crew_results["message"]}
            ]

    return agent_insights


def extract_next_phase(result: Dict[str, Any]) -> Optional[str]:
    """
    Extract next phase from execution result.

    Args:
        result: Execution result dictionary

    Returns:
        Next phase name if available
    """
    # Check multiple locations for next_phase
    next_phase = result.get("result", {}).get("next_phase")
    if not next_phase:
        next_phase = result.get("next_phase")

    return next_phase
