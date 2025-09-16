"""
Data quality confidence factor calculations.

Contains methods for assessing data quality, consistency, format quality, and richness.
"""

import logging
from typing import Any, Dict

from ..models import ConfidenceFactor, ConfidenceFactorType

logger = logging.getLogger(__name__)


class QualityFactorCalculator:
    """Calculator for data quality confidence factors"""

    def __init__(self, factor_weights: Dict, strategy_requirements: Dict):
        self.factor_weights = factor_weights
        self.strategy_requirements = strategy_requirements

    def calculate_quality_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate data quality confidence factor"""
        try:
            quality_indicators = []

            # Check for data validation
            validation_score = collection_metadata.get("validation_score", 0)
            quality_indicators.append(("validation", validation_score))

            # Check for data consistency
            consistency_score = self._assess_data_consistency(asset_data)
            quality_indicators.append(("consistency", consistency_score))

            # Check for data format quality
            format_score = self._assess_data_format_quality(asset_data)
            quality_indicators.append(("format", format_score))

            # Check for data richness (depth of information)
            richness_score = self._assess_data_richness(asset_data)
            quality_indicators.append(("richness", richness_score))

            # Calculate weighted quality score
            total_weight = len(quality_indicators)
            weighted_score = (
                sum(score for _, score in quality_indicators) / total_weight
                if total_weight > 0
                else 0
            )

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.DATA_QUALITY,
                weight=self.factor_weights[ConfidenceFactorType.DATA_QUALITY],
                score=weighted_score,
                evidence={
                    "validation_score": validation_score,
                    "consistency_score": consistency_score,
                    "format_score": format_score,
                    "richness_score": richness_score,
                    "quality_indicators": dict(quality_indicators),
                },
                description=f"Data quality assessment: {weighted_score:.1f}% overall quality",
            )

        except Exception as e:
            logger.error(f"Error calculating quality factor: {e}")
            return self._create_error_factor(ConfidenceFactorType.DATA_QUALITY, str(e))

    def _assess_data_consistency(self, asset_data: Dict[str, Any]) -> float:
        """Assess consistency of data values"""
        consistency_score = 80  # Base score

        # Check for inconsistent naming patterns
        hostname_fields = ["hostname", "server_name", "host_name"]
        hostname_values = [
            asset_data.get(field) for field in hostname_fields if asset_data.get(field)
        ]
        if len(set(hostname_values)) > 1:
            consistency_score -= 20

        # Check for reasonable value ranges
        cpu_cores = asset_data.get("cpu_cores", 0)
        if cpu_cores and (cpu_cores < 1 or cpu_cores > 256):
            consistency_score -= 10

        memory_gb = asset_data.get("memory_gb", 0)
        if memory_gb and (memory_gb < 1 or memory_gb > 2048):
            consistency_score -= 10

        return max(0, consistency_score)

    def _assess_data_format_quality(self, asset_data: Dict[str, Any]) -> float:
        """Assess quality of data formats"""
        format_score = 85  # Base score

        # Check for proper data types
        numeric_fields = ["cpu_cores", "memory_gb", "storage_gb"]
        for field in numeric_fields:
            value = asset_data.get(field)
            if value and not isinstance(value, (int, float)):
                try:
                    float(value)
                except (ValueError, TypeError):
                    format_score -= 10

        return max(0, format_score)

    def _assess_data_richness(self, asset_data: Dict[str, Any]) -> float:
        """Assess richness/depth of data"""
        richness_score = 0

        # Count meaningful fields
        meaningful_fields = sum(
            1 for value in asset_data.values() if value and str(value).strip()
        )

        if meaningful_fields >= 20:
            richness_score = 95
        elif meaningful_fields >= 15:
            richness_score = 85
        elif meaningful_fields >= 10:
            richness_score = 70
        elif meaningful_fields >= 5:
            richness_score = 50
        else:
            richness_score = 30

        return richness_score

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
