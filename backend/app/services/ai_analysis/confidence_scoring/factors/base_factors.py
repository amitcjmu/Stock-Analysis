"""
Base confidence factor calculations.

Contains core factor calculation methods for data completeness and validation status.
"""

import logging
from typing import Any, Dict

from ..models import ConfidenceFactor, ConfidenceFactorType

logger = logging.getLogger(__name__)


class BaseFactorCalculator:
    """Calculator for basic confidence factors"""

    def __init__(self, factor_weights: Dict, strategy_requirements: Dict):
        self.factor_weights = factor_weights
        self.strategy_requirements = strategy_requirements

    def calculate_completeness_factor(
        self, asset_data: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data completeness confidence factor"""
        try:
            # Define critical attributes across all categories
            all_critical_attributes = set()
            for strategy_data in self.strategy_requirements.values():
                all_critical_attributes.update(strategy_data["critical_attributes"])

            # Calculate completeness
            available_attributes = set(
                key
                for key, value in asset_data.items()
                if value is not None and value != "" and value != []
            )

            critical_available = available_attributes.intersection(
                all_critical_attributes
            )
            completeness_percentage = (
                len(critical_available) / len(all_critical_attributes)
            ) * 100

            # Apply quality scoring
            if completeness_percentage >= 90:
                score = 95 + (completeness_percentage - 90) * 0.5
            elif completeness_percentage >= 75:
                score = 80 + (completeness_percentage - 75) * 1.0
            elif completeness_percentage >= 50:
                score = 60 + (completeness_percentage - 50) * 0.8
            else:
                score = completeness_percentage * 1.2

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.DATA_COMPLETENESS,
                weight=self.factor_weights[ConfidenceFactorType.DATA_COMPLETENESS],
                score=min(100.0, max(0.0, score)),
                evidence={
                    "total_critical_attributes": len(all_critical_attributes),
                    "available_attributes": len(critical_available),
                    "completeness_percentage": completeness_percentage,
                    "missing_critical": list(
                        all_critical_attributes - critical_available
                    ),
                },
                description=(
                    f"Data completeness: {len(critical_available)}/"
                    f"{len(all_critical_attributes)} critical attributes"
                ),
            )

        except Exception as e:
            logger.error(f"Error calculating completeness factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.DATA_COMPLETENESS, str(e)
            )

    def calculate_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate validation status confidence factor"""
        try:
            validation_score = 0
            validation_evidence = {}

            # Check for automated validation
            if collection_metadata.get("automated_validation_passed", False):
                validation_score += 40
                validation_evidence["automated_validation"] = True

            # Check for business validation
            if collection_metadata.get("business_validation_passed", False):
                validation_score += 30
                validation_evidence["business_validation"] = True

            # Check for technical validation
            if collection_metadata.get("technical_validation_passed", False):
                validation_score += 20
                validation_evidence["technical_validation"] = True

            # Check for cross-reference validation
            if collection_metadata.get("cross_reference_validated", False):
                validation_score += 10
                validation_evidence["cross_reference_validation"] = True

            # Penalty for validation failures
            validation_failures = collection_metadata.get("validation_failures", [])
            if validation_failures:
                failure_penalty = min(30, len(validation_failures) * 10)
                validation_score -= failure_penalty
                validation_evidence["validation_failures"] = validation_failures

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.VALIDATION_STATUS,
                weight=self.factor_weights[ConfidenceFactorType.VALIDATION_STATUS],
                score=min(100.0, max(0.0, validation_score)),
                evidence=validation_evidence,
                description=f"Validation status: {len(validation_evidence)} validation types completed",
            )

        except Exception as e:
            logger.error(f"Error calculating validation factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.VALIDATION_STATUS, str(e)
            )

    def _create_error_factor(
        self, factor_type: ConfidenceFactorType, error_msg: str
    ) -> ConfidenceFactor:
        """Create error factor when calculation fails"""
        return ConfidenceFactor(
            factor_type=factor_type,
            weight=self.factor_weights[factor_type],
            score=0.0,
            evidence={"error": error_msg},
            description=f"Error calculating {factor_type.value}: {error_msg}",
        )
