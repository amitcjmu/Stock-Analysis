"""
Modular confidence factor calculations.

Provides a unified interface to all confidence factor calculation methods
while maintaining backward compatibility with the existing ConfidenceFactorCalculator.
"""

import logging
from typing import Any, Dict

from .base_factors import BaseFactorCalculator
from .business_factors import BusinessFactorCalculator
from .quality_factors import QualityFactorCalculator
from .technical_factors import TechnicalFactorCalculator
from ..models import ConfidenceFactor, ConfidenceFactorType

logger = logging.getLogger(__name__)


class ConfidenceFactorCalculator:
    """
    Unified confidence factor calculator that delegates to specialized calculators.

    Maintains backward compatibility with the existing API while using
    modular implementations under the hood.
    """

    def __init__(self, factor_weights: Dict, strategy_requirements: Dict):
        self.factor_weights = factor_weights
        self.strategy_requirements = strategy_requirements

        # Initialize specialized calculators
        self.base_calculator = BaseFactorCalculator(
            factor_weights, strategy_requirements
        )
        self.quality_calculator = QualityFactorCalculator(
            factor_weights, strategy_requirements
        )
        self.business_calculator = BusinessFactorCalculator(
            factor_weights, strategy_requirements
        )
        self.technical_calculator = TechnicalFactorCalculator(
            factor_weights, strategy_requirements
        )

    def calculate_completeness_factor(
        self, asset_data: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data completeness confidence factor"""
        return self.base_calculator.calculate_completeness_factor(asset_data)

    def calculate_quality_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data quality confidence factor"""
        return self.quality_calculator.calculate_quality_factor(
            asset_data, collection_metadata
        )

    def calculate_reliability_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate source reliability confidence factor"""
        return self.business_calculator.calculate_reliability_factor(
            collection_metadata
        )

    def calculate_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate validation status confidence factor"""
        return self.base_calculator.calculate_validation_factor(
            asset_data, collection_metadata
        )

    def calculate_business_context_factor(
        self, asset_data: Dict[str, Any], business_context: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate business context confidence factor"""
        return self.business_calculator.calculate_business_context_factor(
            asset_data, business_context
        )

    def calculate_freshness_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate temporal freshness confidence factor"""
        return self.technical_calculator.calculate_freshness_factor(collection_metadata)

    def calculate_cross_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate cross-validation confidence factor"""
        return self.technical_calculator.calculate_cross_validation_factor(
            asset_data, collection_metadata
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


# Export all factor calculation classes for direct access if needed
__all__ = [
    "ConfidenceFactorCalculator",
    "BaseFactorCalculator",
    "QualityFactorCalculator",
    "BusinessFactorCalculator",
    "TechnicalFactorCalculator",
]
