"""
Technical confidence factor calculations.

Contains methods for assessing temporal freshness and cross-validation factors.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from ..models import ConfidenceFactor, ConfidenceFactorType

logger = logging.getLogger(__name__)


class TechnicalFactorCalculator:
    """Calculator for technical confidence factors"""

    def __init__(self, factor_weights: Dict, strategy_requirements: Dict):
        self.factor_weights = factor_weights
        self.strategy_requirements = strategy_requirements

    def calculate_freshness_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate temporal freshness confidence factor"""
        try:
            collection_timestamp = collection_metadata.get("collection_timestamp")
            if not collection_timestamp:
                collection_timestamp = collection_metadata.get("created_at")

            if isinstance(collection_timestamp, str):
                try:
                    collection_time = datetime.fromisoformat(
                        collection_timestamp.replace("Z", "+00:00")
                    )
                except Exception:
                    collection_time = datetime.now(timezone.utc)
            elif isinstance(collection_timestamp, datetime):
                collection_time = collection_timestamp
            else:
                collection_time = datetime.now(timezone.utc)

            # Calculate age in days
            age_days = (datetime.now(timezone.utc) - collection_time).days

            # Freshness scoring based on age
            if age_days <= 1:
                freshness_score = 100
            elif age_days <= 7:
                freshness_score = 95 - (age_days - 1) * 2
            elif age_days <= 30:
                freshness_score = 88 - (age_days - 7) * 1.5
            elif age_days <= 90:
                freshness_score = 55 - (age_days - 30) * 0.5
            else:
                freshness_score = max(20, 25 - (age_days - 90) * 0.1)

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.TEMPORAL_FRESHNESS,
                weight=self.factor_weights[ConfidenceFactorType.TEMPORAL_FRESHNESS],
                score=freshness_score,
                evidence={
                    "collection_timestamp": collection_time.isoformat(),
                    "age_days": age_days,
                    "freshness_category": self._categorize_freshness(age_days),
                },
                description=f"Data freshness: {age_days} days old",
            )

        except Exception as e:
            logger.error(f"Error calculating freshness factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.TEMPORAL_FRESHNESS, str(e)
            )

    def calculate_cross_validation_factor(
        self, asset_data: Dict[str, Any], collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate cross-validation confidence factor"""
        try:
            cross_val_score = 0
            cross_val_evidence = {}

            # Multiple source validation
            source_count = collection_metadata.get("source_count", 1)
            if source_count > 1:
                cross_val_score += min(40, source_count * 15)
                cross_val_evidence["multiple_sources"] = source_count

            # Cross-reference with known systems
            if collection_metadata.get("cmdb_cross_reference", False):
                cross_val_score += 25
                cross_val_evidence["cmdb_cross_reference"] = True

            # Consistency across collection methods
            consistency_score = collection_metadata.get("cross_method_consistency", 0)
            if consistency_score > 0:
                cross_val_score += consistency_score * 0.3
                cross_val_evidence["cross_method_consistency"] = consistency_score

            # Historical data comparison
            if collection_metadata.get("historical_comparison", False):
                cross_val_score += 15
                cross_val_evidence["historical_comparison"] = True

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.CROSS_VALIDATION,
                weight=self.factor_weights[ConfidenceFactorType.CROSS_VALIDATION],
                score=min(100.0, cross_val_score),
                evidence=cross_val_evidence,
                description=f"Cross-validation: {len(cross_val_evidence)} validation types",
            )

        except Exception as e:
            logger.error(f"Error calculating cross-validation factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.CROSS_VALIDATION, str(e)
            )

    def _categorize_freshness(self, age_days: int) -> str:
        """Categorize data freshness based on age"""
        if age_days <= 1:
            return "very_fresh"
        elif age_days <= 7:
            return "fresh"
        elif age_days <= 30:
            return "acceptable"
        elif age_days <= 90:
            return "aging"
        else:
            return "stale"

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
