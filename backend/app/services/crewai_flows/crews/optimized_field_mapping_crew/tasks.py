"""
Task Creation for Optimized Field Mapping Crew

This module contains task creation logic that leverages memory and learning
to create intelligent field mapping tasks.

Extracted from optimized_field_mapping_crew.py to improve maintainability.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from crewai import Agent, Task

from app.services.agent_learning_system import LearningContext

from .memory_helpers import get_similar_data_structures

logger = logging.getLogger(__name__)


async def create_memory_enhanced_tasks(
    crew_base,
    agents: List["Agent"],
    raw_data: List[Dict[str, Any]],
    context: Optional[LearningContext] = None,
) -> List["Task"]:
    """
    Create tasks that leverage memory and learning for field mapping.

    This function creates an enhanced mapping task that:
    - Uses learned mapping patterns from memory
    - Provides context from similar data structures
    - Guides the agent to apply historical knowledge
    - Identifies learning opportunities

    Args:
        crew_base: Instance of OptimizedCrewBase providing optimized task creation
        agents: List of agents (should contain field_mapper agent)
        raw_data: Raw data to be mapped
        context: Learning context for memory retrieval

    Returns:
        List containing the memory-enhanced mapping task
    """
    try:
        if not agents:
            raise ValueError("No agents provided for task creation")

        field_mapper = agents[0]

        # Extract headers and sample data
        headers = list(raw_data[0].keys()) if raw_data else []
        data_sample = raw_data[:3] if raw_data else []

        # Check for similar data structures in memory
        context_info = await get_similar_data_structures(
            headers=headers, context=context, limit=3
        )

        # Enhanced mapping task with memory context
        mapping_task = crew_base.create_optimized_task(
            description=f"""
ENHANCED FIELD MAPPING TASK WITH MEMORY:

Source Headers: {headers}
Sample Data: {json.dumps(data_sample, indent=2)}
{context_info}

YOUR ENHANCED TASK:
1. Analyze source fields against learned patterns
2. Apply memory-based mapping suggestions
3. Use historical confidence scores to guide decisions
4. Create optimized field mappings

MAPPING PROCESS:
1. For each source field, check memory for similar patterns
2. Apply learned mapping rules from past successes
3. Use semantic analysis for new or unclear fields
4. Assign confidence scores based on pattern strength and history
5. Flag uncertain mappings for potential user review

EXPECTED OUTPUT FORMAT:
```json
{{
    "mappings": {{
        "source_field_1": {{
            "target_field": "standard_field_name",
            "confidence": 0.85,
            "reasoning": "Exact match found in memory with 95% success rate",
            "memory_pattern_id": "pattern_id_if_used"
        }}
    }},
    "unmapped_fields": ["field1", "field2"],
    "mapping_summary": {{
        "total_fields": {len(headers)},
        "mapped_fields": 0,
        "avg_confidence": 0.0,
        "memory_patterns_used": 0,
        "new_patterns_identified": 0
    }},
    "learning_opportunities": {{
        "low_confidence_mappings": [],
        "new_field_patterns": [],
        "validation_needed": []
    }}
}}
```

QUALITY REQUIREMENTS:
- Each mapping must have clear reasoning
- Confidence scores must reflect actual certainty
- Flag mappings that need validation
- Identify new patterns for future learning
""",
            agent=field_mapper,
            expected_output=(
                "JSON field mapping result with memory-enhanced confidence scoring "
                "and learning identification"
            ),
            max_execution_time=300,
            human_input=False,
        )

        logger.info("Created memory-enhanced mapping task")
        return [mapping_task]

    except Exception as e:
        logger.error(f"Failed to create memory-enhanced tasks: {e}")
        raise


def create_task_description(
    headers: List[str],
    data_sample: List[Dict[str, Any]],
    context_info: str,
) -> str:
    """
    Create detailed task description for field mapping.

    Args:
        headers: List of source field headers
        data_sample: Sample data records
        context_info: Context information from memory

    Returns:
        Formatted task description string
    """
    return f"""
ENHANCED FIELD MAPPING TASK WITH MEMORY:

Source Headers: {headers}
Sample Data: {json.dumps(data_sample, indent=2)}
{context_info}

YOUR ENHANCED TASK:
1. Analyze source fields against learned patterns
2. Apply memory-based mapping suggestions
3. Use historical confidence scores to guide decisions
4. Create optimized field mappings

MAPPING PROCESS:
1. For each source field, check memory for similar patterns
2. Apply learned mapping rules from past successes
3. Use semantic analysis for new or unclear fields
4. Assign confidence scores based on pattern strength and history
5. Flag uncertain mappings for potential user review

EXPECTED OUTPUT FORMAT:
```json
{{
    "mappings": {{
        "source_field_1": {{
            "target_field": "standard_field_name",
            "confidence": 0.85,
            "reasoning": "Exact match found in memory with 95% success rate",
            "memory_pattern_id": "pattern_id_if_used"
        }}
    }},
    "unmapped_fields": ["field1", "field2"],
    "mapping_summary": {{
        "total_fields": {len(headers)},
        "mapped_fields": 0,
        "avg_confidence": 0.0,
        "memory_patterns_used": 0,
        "new_patterns_identified": 0
    }},
    "learning_opportunities": {{
        "low_confidence_mappings": [],
        "new_field_patterns": [],
        "validation_needed": []
    }}
}}
```

QUALITY REQUIREMENTS:
- Each mapping must have clear reasoning
- Confidence scores must reflect actual certainty
- Flag mappings that need validation
- Identify new patterns for future learning
"""
