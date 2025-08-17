"""
Base reasoning pattern classes and core enums for Agent Intelligence Architecture

This module defines the fundamental building blocks for agent reasoning patterns,
including core enums, data structures, and base classes that all reasoning
patterns inherit from.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from .exceptions import ConfidenceCalculationError

logger = logging.getLogger(__name__)


class ReasoningDimension(str, Enum):
    """Dimensions of asset analysis for agent reasoning"""

    BUSINESS_VALUE = "business_value"
    RISK_ASSESSMENT = "risk_assessment"
    MODERNIZATION_POTENTIAL = "modernization_potential"
    CLOUD_READINESS = "cloud_readiness"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    DEPENDENCY_IMPACT = "dependency_impact"


class ConfidenceLevel(str, Enum):
    """Agent confidence levels in reasoning"""

    VERY_LOW = "very_low"  # 0.0 - 0.2
    LOW = "low"  # 0.2 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.6
    HIGH = "high"  # 0.6 - 0.8
    VERY_HIGH = "very_high"  # 0.8 - 1.0


class EvidenceType(str, Enum):
    """Types of evidence agents can discover"""

    TECHNOLOGY_STACK = "technology_stack"
    USAGE_PATTERNS = "usage_patterns"
    BUSINESS_CRITICALITY = "business_criticality"
    INTEGRATION_COMPLEXITY = "integration_complexity"
    PERFORMANCE_METRICS = "performance_metrics"
    NAMING_CONVENTIONS = "naming_conventions"
    ENVIRONMENT_CONTEXT = "environment_context"


@dataclass
class ReasoningEvidence:
    """Evidence piece used in agent reasoning"""

    evidence_type: EvidenceType
    field_name: str
    field_value: Any
    confidence: float
    reasoning: str
    supporting_patterns: List[str]  # Pattern IDs that support this evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type.value,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "supporting_patterns": self.supporting_patterns,
        }


@dataclass
class AgentReasoning:
    """Complete reasoning result from an agent"""

    dimension: ReasoningDimension
    score: int  # 1-10 for business value, 0-100 for cloud readiness, etc.
    confidence: float  # 0.0 - 1.0
    reasoning_summary: str
    evidence_pieces: List[ReasoningEvidence]
    discovered_patterns: List[Dict[str, Any]]  # New patterns discovered during analysis
    applied_patterns: List[str]  # Pattern IDs that were used in reasoning
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning_summary": self.reasoning_summary,
            "evidence_pieces": [
                evidence.to_dict() for evidence in self.evidence_pieces
            ],
            "discovered_patterns": self.discovered_patterns,
            "applied_patterns": self.applied_patterns,
            "recommendations": self.recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }


class BaseReasoningPattern:
    """
    Base class for all reasoning patterns.
    Provides common functionality for pattern matching, evidence analysis,
    and confidence calculation.
    """

    def __init__(self, pattern_id: str, pattern_name: str, description: str):
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.description = description
        self.logger = logger

    def matches_asset(
        self, asset_data: Dict[str, Any], criteria: Dict[str, Any]
    ) -> bool:
        """
        Check if a pattern matches an asset based on criteria.

        Args:
            asset_data: Asset data to match against
            criteria: Pattern criteria for matching

        Returns:
            True if pattern matches, False otherwise
        """
        try:
            for field, criteria_value in criteria.items():
                asset_value = asset_data.get(field)
                if asset_value is None:
                    continue

                if isinstance(criteria_value, dict):
                    if not self._evaluate_complex_criteria(asset_value, criteria_value):
                        return False
                elif isinstance(criteria_value, list):
                    if not self._evaluate_list_criteria(asset_value, criteria_value):
                        return False
                else:
                    if not self._evaluate_simple_criteria(asset_value, criteria_value):
                        return False

            return True
        except Exception as e:
            self.logger.warning(f"Pattern matching error for {self.pattern_id}: {e}")
            return False

    def _evaluate_complex_criteria(
        self, asset_value: Any, criteria: Dict[str, Any]
    ) -> bool:
        """Evaluate complex criteria with operators"""
        if "operator" in criteria and "value" in criteria:
            operator = criteria["operator"]
            expected_value = criteria["value"]

            if operator == ">=" and isinstance(asset_value, (int, float)):
                return asset_value >= expected_value
            elif operator == "contains" and isinstance(asset_value, str):
                return expected_value.lower() in asset_value.lower()
            elif operator == "contains_any" and isinstance(asset_value, str):
                if isinstance(expected_value, list):
                    return any(
                        item.lower() in asset_value.lower() for item in expected_value
                    )
        return False

    def _evaluate_list_criteria(self, asset_value: Any, criteria: List[Any]) -> bool:
        """Evaluate list-based criteria (any match)"""
        return any(str(item).lower() in str(asset_value).lower() for item in criteria)

    def _evaluate_simple_criteria(self, asset_value: Any, criteria: Any) -> bool:
        """Evaluate simple direct value match"""
        return str(criteria).lower() == str(asset_value).lower()

    def calculate_confidence(self, evidence_pieces: List[ReasoningEvidence]) -> float:
        """
        Calculate overall confidence based on evidence pieces.

        Args:
            evidence_pieces: List of evidence supporting this pattern

        Returns:
            Confidence score between 0.0 and 1.0

        Raises:
            ConfidenceCalculationError: If confidence calculation fails
        """
        try:
            if not evidence_pieces:
                return 0.0

            confidence_values = [evidence.confidence for evidence in evidence_pieces]

            # Weighted average with diminishing returns for additional evidence
            base_confidence = sum(confidence_values) / len(confidence_values)
            evidence_boost = min(0.2, len(evidence_pieces) * 0.05)

            return min(1.0, base_confidence + evidence_boost)
        except Exception as e:
            raise ConfidenceCalculationError(
                f"Failed to calculate confidence: {e}",
                confidence_factors=[e.confidence for e in evidence_pieces],
            )

    def format_reasoning_template(
        self, template: str, asset_data: Dict[str, Any]
    ) -> str:
        """
        Format a reasoning template with asset data.

        Args:
            template: Template string with placeholders
            asset_data: Asset data for placeholder replacement

        Returns:
            Formatted reasoning string
        """
        try:
            return template.format(**asset_data)
        except KeyError as e:
            self.logger.warning(f"Missing field {e} in reasoning template")
            return template
        except Exception as e:
            self.logger.warning(f"Template formatting error: {e}")
            return template


class BaseEvidenceAnalyzer:
    """
    Base class for evidence analysis components.
    Provides common functionality for analyzing different types of evidence.
    """

    def __init__(self, analyzer_name: str):
        self.analyzer_name = analyzer_name
        self.logger = logger

    async def analyze_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """
        Analyze asset data to extract evidence.

        Args:
            asset_data: Asset data to analyze

        Returns:
            List of evidence pieces found
        """
        raise NotImplementedError("Subclasses must implement analyze_evidence")

    def create_evidence(
        self,
        evidence_type: EvidenceType,
        field_name: str,
        field_value: Any,
        confidence: float,
        reasoning: str,
        supporting_patterns: List[str] = None,
    ) -> ReasoningEvidence:
        """
        Create a standardized evidence piece.

        Args:
            evidence_type: Type of evidence
            field_name: Name of the field this evidence relates to
            field_value: Value that provides the evidence
            confidence: Confidence level (0.0 - 1.0)
            reasoning: Human-readable reasoning for this evidence
            supporting_patterns: Pattern IDs that support this evidence

        Returns:
            ReasoningEvidence instance
        """
        return ReasoningEvidence(
            evidence_type=evidence_type,
            field_name=field_name,
            field_value=field_value,
            confidence=confidence,
            reasoning=reasoning,
            supporting_patterns=supporting_patterns or [],
        )


class BasePatternRepository:
    """
    Base class for pattern repositories.
    Manages storage and retrieval of reasoning patterns.
    """

    def __init__(self, repository_name: str):
        self.repository_name = repository_name
        self.patterns = {}
        self.logger = logger

    def add_pattern(
        self,
        pattern_id: str,
        pattern_data: Dict[str, Any],
        confidence_score: float = 0.5,
    ) -> None:
        """
        Add a pattern to the repository.

        Args:
            pattern_id: Unique identifier for the pattern
            pattern_data: Pattern configuration and criteria
            confidence_score: Base confidence for this pattern
        """
        self.patterns[pattern_id] = {
            "id": pattern_id,
            "data": pattern_data,
            "confidence": confidence_score,
            "created_at": datetime.utcnow().isoformat(),
        }

    def get_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """
        Retrieve a pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern data or None if not found
        """
        return self.patterns.get(pattern_id)

    def get_patterns_by_type(self, pattern_type: str) -> List[Dict[str, Any]]:
        """
        Retrieve all patterns of a specific type.

        Args:
            pattern_type: Type of patterns to retrieve

        Returns:
            List of matching patterns
        """
        return [
            pattern
            for pattern in self.patterns.values()
            if pattern["data"].get("pattern_type") == pattern_type
        ]

    def list_all_patterns(self) -> List[Dict[str, Any]]:
        """
        List all patterns in the repository.

        Returns:
            List of all patterns
        """
        return list(self.patterns.values())
