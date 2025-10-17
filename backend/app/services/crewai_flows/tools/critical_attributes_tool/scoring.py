"""
Migration Readiness Scoring Logic

Calculates migration readiness scores for each 6R strategy based on
critical attributes coverage and provides strategy recommendations.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MigrationReadinessScorer:
    """Calculate migration readiness scores based on attribute coverage"""

    @staticmethod
    def calculate_sixr_readiness(
        attribute_coverage: Dict[str, Any], asset_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate readiness scores for each 6R strategy based on attribute coverage

        Args:
            attribute_coverage: Results from critical attributes assessment
            asset_data: Optional asset-specific data for more accurate scoring

        Returns:
            Readiness scores for each 6R strategy with recommendations
        """
        try:
            # Base scores influenced by attribute coverage
            readiness_score = attribute_coverage.get("migration_readiness_score", 0)
            category_coverage = attribute_coverage.get("category_coverage", {})

            sixr_scores = {
                "rehost": {
                    "score": min(
                        100, readiness_score + 20
                    ),  # Easiest, needs least info
                    "confidence": (
                        0.9 if category_coverage.get("infrastructure", 0) >= 4 else 0.5
                    ),
                    "blockers": [],
                    "requirements": ["Basic infrastructure attributes"],
                },
                "replatform": {
                    "score": min(100, readiness_score + 10),
                    "confidence": (
                        0.8 if category_coverage.get("infrastructure", 0) >= 5 else 0.4
                    ),
                    "blockers": [],
                    "requirements": ["Infrastructure and basic application attributes"],
                },
                "refactor": {
                    "score": max(0, readiness_score - 10),
                    "confidence": (
                        0.7 if category_coverage.get("application", 0) >= 6 else 0.3
                    ),
                    "blockers": [],
                    "requirements": [
                        "Complete application attributes",
                        "Technical debt assessment",
                    ],
                },
                "rearchitect": {
                    "score": max(0, readiness_score - 20),
                    "confidence": (
                        0.6 if category_coverage.get("application", 0) >= 7 else 0.2
                    ),
                    "blockers": [],
                    "requirements": [
                        "All application attributes",
                        "Architecture patterns",
                        "Dependencies",
                    ],
                },
                "replace": {
                    "score": readiness_score,  # Neutral, depends on business context
                    "confidence": (
                        0.8 if category_coverage.get("business", 0) >= 3 else 0.4
                    ),
                    "blockers": [],
                    "requirements": ["Business criticality", "Stakeholder impact"],
                },
                "retire": {
                    "score": min(100, readiness_score + 15),  # Simple decommissioning
                    "confidence": (
                        0.9 if category_coverage.get("business", 0) >= 2 else 0.5
                    ),
                    "blockers": [],
                    "requirements": ["Business approval", "Data archival plan"],
                },
            }

            # Add blockers based on missing critical attributes
            missing_critical = attribute_coverage.get("missing_critical", [])
            if "technology_stack" in missing_critical:
                sixr_scores["refactor"]["blockers"].append(
                    "Missing technology stack information"
                )
                sixr_scores["rearchitect"]["blockers"].append(
                    "Cannot assess without technology stack"
                )

            if "business_criticality_score" in missing_critical:
                sixr_scores["replace"]["blockers"].append(
                    "Business criticality unknown"
                )

            if "integration_dependencies" in missing_critical:
                sixr_scores["rearchitect"]["blockers"].append("Dependencies not mapped")

            # Calculate overall recommendation
            best_strategy = max(
                sixr_scores.items(), key=lambda x: x[1]["score"] * x[1]["confidence"]
            )

            return {
                "sixr_scores": sixr_scores,
                "recommended_strategy": best_strategy[0],
                "recommendation_confidence": best_strategy[1]["confidence"],
                "overall_readiness": readiness_score,
                "data_quality_warning": readiness_score < 50,
                "enrichment_needed": readiness_score < 75,
            }

        except Exception as e:
            logger.error(f"❌ 6R readiness scoring failed: {e}")
            return {
                "error": str(e),
                "sixr_scores": {},
                "overall_readiness": 0,
            }
