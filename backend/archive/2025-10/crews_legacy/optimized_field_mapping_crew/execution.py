"""
Execution Logic for Optimized Field Mapping Crew

This module contains the execution orchestration and result processing logic
for the field mapping crew.

Extracted from optimized_field_mapping_crew.py to improve maintainability.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from crewai import Process

from app.services.agent_learning_system import LearningContext
from app.services.performance.response_optimizer import optimize_response

from .agents import create_memory_enhanced_agents
from .memory_helpers import (
    calculate_avg_confidence,
    calculate_confidence_distribution,
    learn_from_mappings,
    store_execution_memory,
)
from .tasks import create_memory_enhanced_tasks

logger = logging.getLogger(__name__)


@optimize_response("field_mapping_execution")
async def execute_enhanced_mapping(
    crew_base,
    raw_data: List[Dict[str, Any]],
    standard_fields: List[str],
    context: Optional[LearningContext] = None,
) -> Dict[str, Any]:
    """
    Execute field mapping with enhanced memory and learning.

    This is the main execution function that:
    1. Creates memory-enhanced agents
    2. Creates memory-enhanced tasks
    3. Executes the crew with performance monitoring
    4. Processes and learns from results
    5. Stores execution memory for future reference

    Args:
        crew_base: Instance of OptimizedCrewBase providing crew infrastructure
        raw_data: Raw data to be mapped
        standard_fields: List of standard CMDB fields to map to
        context: Learning context for tenant scoping

    Returns:
        Dictionary containing mapping results with success/error status
    """
    try:
        # Create memory-enhanced agents and tasks
        agents = await create_memory_enhanced_agents(
            crew_base, standard_fields, context
        )
        tasks = await create_memory_enhanced_tasks(crew_base, agents, raw_data, context)

        # Create optimized crew
        crew = crew_base.create_optimized_crew(
            agents=agents, tasks=tasks, process=Process.sequential
        )

        # Execute with performance monitoring
        logger.info("Starting enhanced field mapping execution")
        result = crew.kickoff()

        # Process and learn from result
        processed_result = await process_mapping_result(result, raw_data, context)

        # Store execution in memory for future reference
        await store_execution_memory(raw_data, processed_result, context)

        logger.info(
            f"Enhanced field mapping completed with {len(processed_result.get('mappings', {}))} mappings"
        )
        return processed_result

    except Exception as e:
        logger.error(f"Enhanced field mapping execution failed: {e}")
        return {
            "error": str(e),
            "success": False,
            "mappings": {},
            "execution_type": "enhanced_memory",
        }


async def process_mapping_result(
    raw_result: Any,
    raw_data: List[Dict[str, Any]],
    context: Optional[LearningContext] = None,
) -> Dict[str, Any]:
    """
    Process and validate mapping result from crew execution.

    This function:
    - Parses raw result (handles both string and dict formats)
    - Extracts JSON from text responses
    - Validates result structure
    - Calculates confidence distributions
    - Learns from successful mappings

    Args:
        raw_result: Raw result from crew execution
        raw_data: Original data used for mapping
        context: Learning context for tenant scoping

    Returns:
        Processed and validated mapping result
    """
    try:
        # Parse result if it's a string
        if isinstance(raw_result, str):
            parsed_result = parse_json_result(raw_result)
        else:
            parsed_result = raw_result

        # Validate and enhance result structure
        processed_result = {
            "success": True,
            "mappings": parsed_result.get("mappings", {}),
            "unmapped_fields": parsed_result.get("unmapped_fields", []),
            "mapping_summary": parsed_result.get("mapping_summary", {}),
            "learning_opportunities": parsed_result.get("learning_opportunities", {}),
            "execution_type": "enhanced_memory",
            "memory_patterns_used": parsed_result.get("mapping_summary", {}).get(
                "memory_patterns_used", 0
            ),
            "confidence_distribution": calculate_confidence_distribution(
                parsed_result.get("mappings", {})
            ),
            "learning_integration": True,
        }

        # Learn from successful mappings
        await learn_from_mappings(processed_result["mappings"], raw_data, context)

        return processed_result

    except Exception as e:
        logger.error(f"Failed to process mapping result: {e}")
        return {
            "error": f"Result processing failed: {str(e)}",
            "success": False,
            "mappings": {},
            "raw_result": str(raw_result)[:500],
            "execution_type": "enhanced_memory",
        }


def parse_json_result(raw_result: str) -> Dict[str, Any]:
    """
    Parse JSON from string result.

    Handles both:
    - Direct JSON strings
    - JSON embedded in markdown code blocks

    Args:
        raw_result: String containing JSON result

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        # Try direct JSON parsing first
        return json.loads(raw_result)
    except json.JSONDecodeError:
        # Extract JSON from text response (markdown code block)
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            raise ValueError("Could not parse JSON from result")


def validate_mapping_result(result: Dict[str, Any]) -> bool:
    """
    Validate that mapping result has required structure.

    Args:
        result: Mapping result to validate

    Returns:
        True if result is valid, False otherwise
    """
    required_fields = ["mappings", "unmapped_fields", "mapping_summary"]

    for field in required_fields:
        if field not in result:
            logger.warning(f"Missing required field in mapping result: {field}")
            return False

    if not isinstance(result["mappings"], dict):
        logger.warning("Mappings field is not a dictionary")
        return False

    return True


def extract_mapping_metrics(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metrics from mapping result.

    Args:
        result: Processed mapping result

    Returns:
        Dictionary of key metrics
    """
    mappings = result.get("mappings", {})

    return {
        "total_mappings": len(mappings),
        "avg_confidence": calculate_avg_confidence(mappings),
        "confidence_distribution": calculate_confidence_distribution(mappings),
        "unmapped_count": len(result.get("unmapped_fields", [])),
        "memory_patterns_used": result.get("memory_patterns_used", 0),
        "learning_opportunities": len(
            result.get("learning_opportunities", {}).get("low_confidence_mappings", [])
        ),
    }
