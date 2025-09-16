"""
Business and reliability confidence factor calculations.

Contains methods for assessing business context and source reliability factors.
"""

import logging
from typing import Any, Dict

from ..models import ConfidenceFactor, ConfidenceFactorType

logger = logging.getLogger(__name__)


class BusinessFactorCalculator:
    """Calculator for business and reliability confidence factors"""

    def __init__(self, factor_weights: Dict, strategy_requirements: Dict):
        self.factor_weights = factor_weights
        self.strategy_requirements = strategy_requirements

    def calculate_business_context_factor(
        self, asset_data: Dict[str, Any], business_context: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate business context confidence factor"""
        try:
            context_score = 0
            context_evidence = {}

            # Business criticality defined
            if business_context.get("business_criticality"):
                context_score += 25
                context_evidence["business_criticality"] = business_context[
                    "business_criticality"
                ]

            # Cost center and ownership
            if business_context.get("cost_center") or asset_data.get("cost_center"):
                context_score += 20
                context_evidence["cost_center"] = True

            # Compliance and regulatory context
            if business_context.get("compliance_requirements") or asset_data.get(
                "compliance_scope"
            ):
                context_score += 20
                context_evidence["compliance_context"] = True

            # Business function and purpose
            if business_context.get("business_function") or asset_data.get(
                "business_function"
            ):
                context_score += 15
                context_evidence["business_function"] = True

            # Stakeholder information
            if business_context.get("stakeholders") or business_context.get(
                "business_owner"
            ):
                context_score += 10
                context_evidence["stakeholder_info"] = True

            # Strategic importance
            if business_context.get("strategic_importance"):
                context_score += 10
                context_evidence["strategic_importance"] = business_context[
                    "strategic_importance"
                ]

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.BUSINESS_CONTEXT,
                weight=self.factor_weights[ConfidenceFactorType.BUSINESS_CONTEXT],
                score=context_score,
                evidence=context_evidence,
                description=f"Business context completeness: {len(context_evidence)} context elements",
            )

        except Exception as e:
            logger.error(f"Error calculating business context factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.BUSINESS_CONTEXT, str(e)
            )

    def calculate_reliability_factor(
        self, collection_metadata: Dict[str, Any]
    ) -> ConfidenceFactor:
        """Calculate source reliability confidence factor"""
        try:
            # Source type reliability scores
            source_reliability_scores = {
                "api_automated": 90,
                "database_export": 85,
                "configuration_file": 80,
                "monitoring_system": 85,
                "cmdb_system": 75,
                "manual_expert": 70,
                "manual_survey": 60,
                "documentation": 50,
                "estimation": 30,
            }

            collection_method = collection_metadata.get(
                "collection_method", "manual_survey"
            )
            base_reliability = source_reliability_scores.get(collection_method, 50)

            # Adjust based on collection metadata
            automation_tier = collection_metadata.get("automation_tier", "tier_3")
            tier_multipliers = {
                "tier_1": 1.1,  # Fully automated - bonus
                "tier_2": 1.05,  # Hybrid - slight bonus
                "tier_3": 1.0,  # Manual with some automation
                "tier_4": 0.95,  # Mostly manual - slight penalty
            }

            reliability_score = base_reliability * tier_multipliers.get(
                automation_tier, 1.0
            )

            # Consider data source credibility
            source_credibility = collection_metadata.get("source_credibility", "medium")
            credibility_adjustments = {
                "high": 1.1,
                "medium": 1.0,
                "low": 0.9,
                "unknown": 0.85,
            }

            reliability_score *= credibility_adjustments.get(source_credibility, 1.0)

            return ConfidenceFactor(
                factor_type=ConfidenceFactorType.SOURCE_RELIABILITY,
                weight=self.factor_weights[ConfidenceFactorType.SOURCE_RELIABILITY],
                score=min(100.0, max(0.0, reliability_score)),
                evidence={
                    "collection_method": collection_method,
                    "automation_tier": automation_tier,
                    "source_credibility": source_credibility,
                    "base_reliability": base_reliability,
                },
                description=f"Source reliability: {collection_method} with {automation_tier} automation",
            )

        except Exception as e:
            logger.error(f"Error calculating reliability factor: {e}")
            return self._create_error_factor(
                ConfidenceFactorType.SOURCE_RELIABILITY, str(e)
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
