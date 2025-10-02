"""
Optimized Field Mapping Crew - Main Class

This module contains the main OptimizedFieldMappingCrew class that orchestrates
field mapping operations with enhanced memory and learning capabilities.

Extracted from optimized_field_mapping_crew.py to improve maintainability.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.agent_learning_system import LearningContext

from ..optimized_crew_base import OptimizedCrewBase
from .agents import get_standard_fields
from .execution import execute_enhanced_mapping
from .memory_helpers import get_mapping_intelligence_report

logger = logging.getLogger(__name__)


class OptimizedFieldMappingCrew(OptimizedCrewBase):
    """
    Optimized Field Mapping Crew with enhanced memory and learning.

    This crew extends OptimizedCrewBase to provide:
    - Enhanced memory integration for pattern recognition
    - Learning from previous mapping experiences
    - Intelligent caching for improved performance
    - Fast execution with learning capabilities

    The crew operates sequentially (not parallel) to ensure field mapping accuracy
    and maintains historical mapping patterns for continuous improvement.

    Attributes:
        crewai_service: The CrewAI service instance
        context: Learning context for tenant scoping and memory access
        enable_memory: Flag to enable/disable memory features
        enable_caching: Flag to enable/disable response caching
        enable_parallel: Flag for parallel execution (disabled for field mapping)
        standard_fields: List of standard CMDB field names

    Example:
        >>> crew = OptimizedFieldMappingCrew(crewai_service, context)
        >>> result = await crew.execute_enhanced_mapping(raw_data)
        >>> print(f"Mapped {len(result['mappings'])} fields")
    """

    def __init__(self, crewai_service, context: Optional[LearningContext] = None):
        """
        Initialize the Optimized Field Mapping Crew.

        Args:
            crewai_service: The CrewAI service instance providing LLM and infrastructure
            context: Optional learning context for tenant-scoped memory access
        """
        super().__init__(
            crewai_service,
            context=context,
            enable_memory=True,
            enable_caching=True,
            enable_parallel=False,  # Sequential for field mapping accuracy
        )

        # Field mapping specific settings
        self.standard_fields = get_standard_fields()

        logger.info(
            f"Optimized Field Mapping Crew initialized with {len(self.standard_fields)} standard fields"
        )

    async def execute_enhanced_mapping(
        self, raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute field mapping with enhanced memory and learning.

        This is the main entry point for field mapping operations. It orchestrates
        the entire mapping process including:
        - Memory-enhanced agent creation
        - Intelligent task generation with learned patterns
        - Crew execution with performance monitoring
        - Result processing and learning
        - Memory storage for future improvements

        Args:
            raw_data: List of dictionaries containing raw data to be mapped

        Returns:
            Dictionary containing:
                - success: Boolean indicating operation success
                - mappings: Dictionary of field mappings with confidence scores
                - unmapped_fields: List of fields that couldn't be mapped
                - mapping_summary: Summary statistics
                - learning_opportunities: Identified opportunities for improvement
                - confidence_distribution: Distribution of confidence scores
                - execution_type: Type of execution used ("enhanced_memory")

        Example:
            >>> raw_data = [
            ...     {"ServerName": "srv-01", "OS": "Linux", "IP": "10.0.0.1"},
            ...     {"ServerName": "srv-02", "OS": "Windows", "IP": "10.0.0.2"}
            ... ]
            >>> result = await crew.execute_enhanced_mapping(raw_data)
            >>> print(result["mappings"])
            {
                "ServerName": {
                    "target_field": "asset_name",
                    "confidence": 0.95,
                    "reasoning": "Exact match from historical patterns"
                },
                ...
            }
        """
        return await execute_enhanced_mapping(
            crew_base=self,
            raw_data=raw_data,
            standard_fields=self.standard_fields,
            context=self.context,
        )

    async def get_mapping_intelligence_report(self) -> Dict[str, Any]:
        """
        Get intelligence report on mapping patterns and performance.

        This method generates a comprehensive report analyzing:
        - Memory system statistics and usage
        - Mapping pattern distributions
        - Confidence trends over time
        - Performance metrics
        - Intelligent recommendations for improvement

        Returns:
            Dictionary containing:
                - memory_overview: Memory system statistics
                - mapping_patterns: Pattern analysis and distribution
                - performance_metrics: Execution performance data
                - recommendations: List of actionable recommendations

        Example:
            >>> report = await crew.get_mapping_intelligence_report()
            >>> print(f"Total patterns learned: {report['mapping_patterns']['total_patterns']}")
            >>> for rec in report['recommendations']:
            ...     print(f"- {rec}")
        """
        return await get_mapping_intelligence_report(
            context=self.context, performance_metrics=self.performance_metrics
        )

    def get_standard_field_list(self) -> List[str]:
        """
        Get the list of standard CMDB fields used for mapping.

        Returns:
            List of standard field names

        Example:
            >>> crew = OptimizedFieldMappingCrew(service)
            >>> fields = crew.get_standard_field_list()
            >>> print(f"Supports {len(fields)} standard fields")
        """
        return self.standard_fields.copy()

    async def validate_mapping_confidence(
        self, mappings: Dict[str, Any], threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Validate that mapping confidence scores meet a minimum threshold.

        This method analyzes mapping results and identifies mappings that fall
        below the specified confidence threshold, which may require manual review.

        Args:
            mappings: Dictionary of field mappings with confidence scores
            threshold: Minimum confidence threshold (default: 0.7)

        Returns:
            Dictionary containing:
                - valid_mappings: Mappings above threshold
                - low_confidence_mappings: Mappings below threshold
                - needs_review: List of fields needing manual review
                - validation_summary: Summary statistics

        Example:
            >>> result = await crew.execute_enhanced_mapping(raw_data)
            >>> validation = await crew.validate_mapping_confidence(result['mappings'])
            >>> if validation['needs_review']:
            ...     print(f"Review needed for: {validation['needs_review']}")
        """
        valid_mappings = {}
        low_confidence_mappings = {}
        needs_review = []

        for source_field, mapping_info in mappings.items():
            confidence = mapping_info.get("confidence", 0.0)

            if confidence >= threshold:
                valid_mappings[source_field] = mapping_info
            else:
                low_confidence_mappings[source_field] = mapping_info
                needs_review.append(
                    {
                        "source_field": source_field,
                        "target_field": mapping_info.get("target_field"),
                        "confidence": confidence,
                        "reasoning": mapping_info.get("reasoning", ""),
                    }
                )

        return {
            "valid_mappings": valid_mappings,
            "low_confidence_mappings": low_confidence_mappings,
            "needs_review": needs_review,
            "validation_summary": {
                "total_mappings": len(mappings),
                "valid_count": len(valid_mappings),
                "low_confidence_count": len(low_confidence_mappings),
                "threshold": threshold,
            },
        }

    async def apply_user_feedback(
        self, source_field: str, target_field: str, is_correct: bool
    ) -> None:
        """
        Apply user feedback to improve future mappings.

        This method stores user corrections and confirmations in memory,
        which will be used to improve future mapping accuracy.

        Args:
            source_field: The source field name
            target_field: The mapped target field name
            is_correct: Whether the mapping was correct (True) or incorrect (False)

        Example:
            >>> # User confirms a mapping is correct
            >>> await crew.apply_user_feedback("ServerName", "asset_name", True)
            >>>
            >>> # User corrects a mapping
            >>> await crew.apply_user_feedback("OS_Type", "operating_system", False)
        """
        from app.services.enhanced_agent_memory import enhanced_agent_memory

        try:
            # Store user feedback in memory
            await enhanced_agent_memory.store_memory(
                {
                    "type": "user_feedback",
                    "source_field": source_field,
                    "target_field": target_field,
                    "is_correct": is_correct,
                    "feedback_type": "mapping_validation",
                },
                memory_type="user_feedback",
                context=self.context,
                metadata={
                    "confidence_score": 1.0 if is_correct else 0.0,
                    "validation_status": "confirmed" if is_correct else "corrected",
                },
            )

            logger.info(
                f"User feedback applied: {source_field} -> {target_field} "
                f"({'correct' if is_correct else 'incorrect'})"
            )

        except Exception as e:
            logger.error(f"Failed to apply user feedback: {e}")
