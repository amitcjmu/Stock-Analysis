"""
GapAnalyzer weighted completeness calculations.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, Dict

from app.services.gap_detection.schemas import DataRequirements

logger = logging.getLogger(__name__)


class CalculationsMixin:
    """Mixin for weighted completeness calculations."""

    def _calculate_weighted_completeness(
        self,
        column_gaps: Any,
        enrichment_gaps: Any,
        jsonb_gaps: Any,
        application_gaps: Any,
        standards_gaps: Any,
        requirements: DataRequirements,
    ) -> tuple[float, Dict[str, float]]:
        """
        Calculate weighted completeness score across all layers.

        Uses priority_weights from DataRequirements to weight each layer's score.
        Weights are normalized to sum to 1.0 before calculation.
        Scores are clamped to [0.0, 1.0] for JSON safety (GPT-5 Rec #8).

        Formula:
            normalized_weight[layer] = weight[layer] / sum(all_weights)
            overall = sum(score[layer] * normalized_weight[layer] for all layers)

        Args:
            column_gaps: ColumnGapReport
            enrichment_gaps: EnrichmentGapReport
            jsonb_gaps: JSONBGapReport
            application_gaps: ApplicationGapReport
            standards_gaps: StandardsGapReport
            requirements: DataRequirements with priority_weights

        Returns:
            Tuple of (overall_completeness, weighted_scores_dict)
            - overall_completeness: float [0.0-1.0]
            - weighted_scores: Dict mapping layer name to normalized weighted contribution

        Note:
            All scores are clamped to [0.0, 1.0] to prevent NaN/Infinity issues.
            Weights are normalized so they sum to 1.0.
        """
        weights = requirements.priority_weights

        # Get individual scores (already clamped by Pydantic Field constraints)
        scores = {
            "columns": column_gaps.completeness_score,
            "enrichments": enrichment_gaps.completeness_score,
            "jsonb": jsonb_gaps.completeness_score,
            "application": application_gaps.completeness_score,
            "standards": standards_gaps.completeness_score,
        }

        # Normalize weights to sum to 1.0
        total_weight = sum(weights.get(layer, 0.0) for layer in scores)
        if total_weight == 0:
            # Avoid division by zero - equal weights
            normalized_weights = {layer: 1.0 / len(scores) for layer in scores}
        else:
            normalized_weights = {
                layer: weights.get(layer, 0.0) / total_weight for layer in scores
            }

        # Calculate weighted score for each layer (contribution to overall)
        weighted_scores = {
            layer: scores[layer] * normalized_weights[layer] for layer in scores
        }

        # Calculate overall completeness (sum of weighted contributions)
        overall = sum(weighted_scores.values())

        # Clamp to [0.0, 1.0] for JSON safety (GPT-5 Rec #8)
        # Note: Should already be in range due to normalization, but clamp for safety
        overall = max(0.0, min(1.0, overall))

        logger.debug(
            "Calculated weighted completeness",
            extra={
                "overall_completeness": overall,
                "weighted_scores": weighted_scores,
                "normalized_weights": normalized_weights,
                "raw_weights": weights,
                "raw_scores": scores,
            },
        )

        return overall, weighted_scores
