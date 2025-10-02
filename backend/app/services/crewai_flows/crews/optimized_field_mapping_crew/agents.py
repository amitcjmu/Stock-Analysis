"""
Agent Creation for Optimized Field Mapping Crew

This module contains agent creation logic with memory-enhanced capabilities.
Creates specialized field mapping agents that leverage learned patterns and
historical mapping data.

Extracted from optimized_field_mapping_crew.py to improve maintainability.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from crewai import Agent

from app.services.agent_learning_system import LearningContext

from .memory_helpers import get_past_mapping_experiences

logger = logging.getLogger(__name__)


async def create_memory_enhanced_agents(
    crew_base,
    standard_fields: List[str],
    context: Optional[LearningContext] = None,
) -> List["Agent"]:
    """
    Create agents with memory-enhanced capabilities for field mapping.

    This function creates the primary field mapping agent with access to:
    - Previous successful mapping patterns from memory
    - Learning from user feedback and corrections
    - Pattern recognition across similar data sources
    - Confidence scoring based on historical accuracy

    Args:
        crew_base: Instance of OptimizedCrewBase providing optimized agent creation
        standard_fields: List of standard CMDB field names to map to
        context: Learning context for memory retrieval (tenant scoping)

    Returns:
        List containing the memory-enhanced field mapper agent
    """
    try:
        # Load previous field mapping experiences from memory
        mapping_experience = await get_past_mapping_experiences(
            context=context, limit=10
        )

        # Primary Field Mapping Agent with memory enhancement
        field_mapper = crew_base.create_optimized_agent(
            role="Enhanced CMDB Field Mapping Specialist",
            goal="Map source data fields to standard CMDB attributes using learned patterns and memory",
            backstory=f"""You are an expert field mapping specialist with access to
organizational memory and learned patterns.

YOUR ENHANCED CAPABILITIES:
- Access to previous successful mapping patterns
- Learning from user feedback and corrections
- Pattern recognition across similar data sources
- Confidence scoring based on historical accuracy

STANDARD TARGET FIELDS:
{', '.join(standard_fields)}

MAPPING APPROACH:
1. First check if similar fields were mapped before (use memory)
2. Apply learned patterns from past successful mappings
3. Use semantic similarity for new field types
4. Assign confidence scores based on match quality and historical accuracy

CONFIDENCE SCORING RULES:
- 0.95+: Exact match with high historical success
- 0.90+: Semantic match with confirmed past success
- 0.80+: Strong pattern match with good history
- 0.70+: Semantic similarity with some history
- 0.60+: Possible match with limited history
- 0.50+: Weak similarity or new pattern
- <0.50: No clear match or unreliable pattern

{mapping_experience}

WORK EFFICIENTLY:
- Leverage memory patterns first
- Make decisions based on learned experience
- Complete mapping in under 45 seconds
- Focus on accuracy through learning, not speed alone
""",
            max_execution_time=300,
            allow_delegation=False,
            tools=[],
        )

        logger.info("Created memory-enhanced field mapping agent")
        return [field_mapper]

    except Exception as e:
        logger.error(f"Failed to create memory-enhanced agents: {e}")
        raise


def get_standard_fields() -> List[str]:
    """
    Get the list of standard CMDB field names.

    Returns:
        List of standard field names used in CMDB mapping
    """
    return [
        "asset_name",
        "asset_type",
        "asset_id",
        "environment",
        "business_criticality",
        "operating_system",
        "ip_address",
        "owner",
        "location",
        "status",
        "description",
        "notes",
    ]
