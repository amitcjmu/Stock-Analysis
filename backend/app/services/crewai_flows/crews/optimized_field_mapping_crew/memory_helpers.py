"""
Memory Integration Helpers for Optimized Field Mapping Crew

This module contains all memory-related integration functions including:
- Memory retrieval for learned mapping patterns
- Memory storage for successful mappings
- Execution memory tracking
- Intelligence report generation

Extracted from optimized_field_mapping_crew.py to improve maintainability.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.enhanced_agent_memory import enhanced_agent_memory

logger = logging.getLogger(__name__)


async def get_past_mapping_experiences(
    context: Optional[LearningContext] = None, limit: int = 10
) -> str:
    """
    Retrieve past successful field mapping experiences from memory.

    Args:
        context: Learning context for tenant scoping
        limit: Maximum number of experiences to retrieve

    Returns:
        Formatted string of mapping experiences for agent prompt
    """
    try:
        past_mappings = await enhanced_agent_memory.retrieve_memories(
            {"type": "field_mapping", "success": True},
            context=context,
            limit=limit,
            memory_types=["field_mapping", "user_feedback"],
        )

        if not past_mappings:
            return ""

        experiences = []
        for memory in past_mappings:
            content = memory.content
            if "source_field" in content and "target_field" in content:
                experiences.append(
                    f"- {content['source_field']} → {content['target_field']} "
                    f"(confidence: {memory.confidence_score:.2f})"
                )

        if not experiences:
            return ""

        return f"""

LEARNED MAPPING PATTERNS (from {len(experiences)} past experiences):
{chr(10).join(experiences[:5])}  # Show top 5
        """

    except Exception as e:
        logger.error(f"Failed to get past mapping experiences: {e}")
        return ""


async def get_similar_data_structures(
    headers: List[str], context: Optional[LearningContext] = None, limit: int = 3
) -> str:
    """
    Retrieve similar data structures from memory.

    Args:
        headers: List of field headers to match against
        context: Learning context for tenant scoping
        limit: Maximum number of similar structures to retrieve

    Returns:
        Formatted string of similar structures for agent context
    """
    try:
        similar_structures = await enhanced_agent_memory.retrieve_memories(
            {
                "type": "data_structure",
                "field_count": len(headers),
                "sample_fields": headers[:5],
            },
            context=context,
            limit=limit,
        )

        if not similar_structures:
            return ""

        return f"""

SIMILAR DATA STRUCTURES FOUND IN MEMORY:
{json.dumps([s.content for s in similar_structures], indent=2)}
        """

    except Exception as e:
        logger.error(f"Failed to get similar data structures: {e}")
        return ""


async def learn_from_mappings(
    mappings: Dict[str, Any],
    raw_data: List[Dict[str, Any]],
    context: Optional[LearningContext] = None,
) -> None:
    """
    Learn from successful mappings for future use.

    Stores mapping patterns in both enhanced agent memory and the existing
    learning system for comprehensive learning integration.

    Args:
        mappings: Dictionary of field mappings with confidence scores
        raw_data: Original raw data used for mapping
        context: Learning context for tenant scoping
    """
    try:
        for source_field, mapping_info in mappings.items():
            target_field = mapping_info.get("target_field")
            confidence = mapping_info.get("confidence", 0.0)

            # Store field mapping pattern in memory
            await enhanced_agent_memory.store_memory(
                {
                    "type": "field_mapping",
                    "source_field": source_field,
                    "target_field": target_field,
                    "confidence": confidence,
                    "reasoning": mapping_info.get("reasoning", ""),
                    "success": True,
                    "data_context": {
                        "total_fields": len(raw_data[0].keys()) if raw_data else 0,
                        "sample_values": (
                            raw_data[0].get(source_field)
                            if raw_data and source_field in raw_data[0]
                            else None
                        ),
                    },
                },
                memory_type="field_mapping",
                context=context,
                metadata={
                    "confidence_score": confidence,
                    "mapping_type": "automatic",
                    "validation_status": "pending",
                },
            )

            # Also store in the existing learning system
            await agent_learning_system.learn_field_mapping_pattern(
                {
                    "original_field": source_field,
                    "mapped_field": target_field,
                    "confidence": confidence,
                    "field_type": mapping_info.get("field_type", "unknown"),
                    "validation_result": True,
                },
                context=context,
            )

        logger.info(f"Learned from {len(mappings)} field mappings")

    except Exception as e:
        logger.error(f"Failed to learn from mappings: {e}")


async def store_execution_memory(
    raw_data: List[Dict[str, Any]],
    result: Dict[str, Any],
    context: Optional[LearningContext] = None,
) -> None:
    """
    Store execution details in memory for future optimization.

    Args:
        raw_data: Original data used for mapping
        result: Mapping result with performance metrics
        context: Learning context for tenant scoping
    """
    try:
        execution_memory = {
            "type": "execution_result",
            "crew_type": "optimized_field_mapping",
            "data_characteristics": {
                "field_count": len(raw_data[0].keys()) if raw_data else 0,
                "record_count": len(raw_data),
                "field_names": list(raw_data[0].keys()) if raw_data else [],
            },
            "performance": {
                "success": result.get("success", False),
                "mapped_fields": len(result.get("mappings", {})),
                "avg_confidence": calculate_avg_confidence(result.get("mappings", {})),
                "memory_patterns_used": result.get("memory_patterns_used", 0),
            },
            "execution_timestamp": datetime.utcnow().isoformat(),
        }

        await enhanced_agent_memory.store_memory(
            execution_memory,
            memory_type="execution_result",
            context=context,
            metadata={
                "execution_type": "field_mapping",
                "optimization_level": "enhanced",
            },
        )

    except Exception as e:
        logger.error(f"Failed to store execution memory: {e}")


def calculate_avg_confidence(mappings: Dict[str, Any]) -> float:
    """
    Calculate average confidence across all mappings.

    Args:
        mappings: Dictionary of field mappings with confidence scores

    Returns:
        Average confidence score (0.0 if no mappings)
    """
    if not mappings:
        return 0.0

    confidences = [mapping.get("confidence", 0.0) for mapping in mappings.values()]
    return sum(confidences) / len(confidences) if confidences else 0.0


def calculate_confidence_distribution(mappings: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate distribution of confidence scores.

    Args:
        mappings: Dictionary of field mappings with confidence scores

    Returns:
        Dictionary with counts of high/medium/low confidence mappings
    """
    distribution = {"high": 0, "medium": 0, "low": 0}

    for mapping_info in mappings.values():
        confidence = mapping_info.get("confidence", 0.0)
        if confidence >= 0.8:
            distribution["high"] += 1
        elif confidence >= 0.6:
            distribution["medium"] += 1
        else:
            distribution["low"] += 1

    return distribution


async def get_mapping_intelligence_report(
    context: Optional[LearningContext] = None,
    performance_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate intelligence report on mapping patterns and performance.

    Args:
        context: Learning context for tenant scoping
        performance_metrics: Performance metrics from crew execution

    Returns:
        Comprehensive intelligence report
    """
    try:
        # Get memory statistics
        memory_stats = enhanced_agent_memory.get_memory_statistics()

        # Get field mapping specific memories
        mapping_memories = await enhanced_agent_memory.retrieve_memories(
            {"type": "field_mapping"}, context=context, limit=100
        )

        # Analyze patterns
        field_patterns = defaultdict(list)
        confidence_trends = []

        for memory in mapping_memories:
            content = memory.content
            source_field = content.get("source_field", "")
            target_field = content.get("target_field", "")
            confidence = memory.confidence_score

            field_patterns[target_field].append(
                {"source": source_field, "confidence": confidence}
            )
            confidence_trends.append(confidence)

        # Calculate intelligence metrics
        report = {
            "memory_overview": memory_stats,
            "mapping_patterns": {
                "total_patterns": len(mapping_memories),
                "unique_targets": len(field_patterns),
                "avg_confidence": (
                    sum(confidence_trends) / len(confidence_trends)
                    if confidence_trends
                    else 0.0
                ),
                "pattern_distribution": dict(field_patterns),
            },
            "performance_metrics": performance_metrics or {},
            "recommendations": await generate_intelligence_recommendations(
                field_patterns, confidence_trends, performance_metrics or {}
            ),
        }

        return report

    except Exception as e:
        logger.error(f"Failed to generate intelligence report: {e}")
        return {"error": str(e)}


async def generate_intelligence_recommendations(
    field_patterns: Dict[str, List[Dict]],
    confidence_trends: List[float],
    performance_metrics: Dict[str, Any],
) -> List[str]:
    """
    Generate intelligent recommendations for mapping improvement.

    Args:
        field_patterns: Mapping patterns by target field
        confidence_trends: List of confidence scores
        performance_metrics: Performance metrics from crew

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    try:
        # Analyze confidence trends
        if confidence_trends:
            avg_confidence = sum(confidence_trends) / len(confidence_trends)
            if avg_confidence < 0.7:
                recommendations.append(
                    "Consider gathering more training data - average confidence is below optimal threshold"
                )

        # Analyze pattern consistency
        inconsistent_patterns = []
        for target, patterns in field_patterns.items():
            if len(patterns) > 1:
                confidences = [p["confidence"] for p in patterns]
                confidence_variance = max(confidences) - min(confidences)
                if confidence_variance > 0.3:
                    inconsistent_patterns.append(target)

        if inconsistent_patterns:
            recommendations.append(
                f"Review mapping consistency for: {', '.join(inconsistent_patterns[:3])}"
            )

        # Performance recommendations
        if performance_metrics.get("avg_task_duration", 0) > 45:
            recommendations.append(
                "Consider enabling more aggressive caching to improve response times"
            )

        if performance_metrics.get("memory_hits", 0) < 5:
            recommendations.append(
                "Memory system is underutilized - consider pre-loading more patterns"
            )

        return recommendations

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        return ["Unable to generate recommendations due to analysis error"]
