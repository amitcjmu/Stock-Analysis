"""
Gap Analysis Tools
Tools for analyzing data gaps in assets and prioritizing them.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class GapAnalysisTool:
    """Tool for analyzing data gaps in assets."""

    def __init__(self):
        self.name = "gap_analysis"
        self.description = "Analyze assets to identify data gaps and prioritize them"

    async def _arun(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async method for analyzing an asset to identify and prioritize data gaps.
        This is the PRIMARY method called by agents.

        Args:
            asset_data: Asset information including mapped and unmapped data

        Returns:
            Gap analysis results with prioritized gaps
        """
        return self._run(asset_data)

    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an asset to identify and prioritize data gaps.

        Args:
            asset_data: Asset information including mapped and unmapped data

        Returns:
            Gap analysis results with prioritized gaps
        """
        gaps = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        # Check for missing critical fields
        # ONLY include fields that need to be COLLECTED from users
        # Computed fields (six_r_strategy, migration_complexity) are excluded
        critical_fields = [
            "business_owner",  # Essential for accountability
            "technical_owner",  # Essential for technical decisions
            "dependencies",  # Critical for sequencing
            "operating_system",  # Critical for compatibility
        ]

        for field in critical_fields:
            if not asset_data.get(field):
                gaps["critical"].append(
                    {
                        "type": "missing_field",
                        "field": field,
                        "description": f"Missing {field.replace('_', ' ')}",
                        "impact": "Blocks migration planning",
                    }
                )

        # Check for unmapped attributes
        unmapped_attrs = asset_data.get("unmapped_attributes", {})
        if unmapped_attrs:
            for attr_name, attr_info in unmapped_attrs.items():
                gaps["medium"].append(
                    {
                        "type": "unmapped_attribute",
                        "field": attr_name,
                        "description": f"Unmapped attribute: {attr_name}",
                        "value": str(attr_info.get("value", ""))[:50],
                        "suggested_mapping": attr_info.get("suggested_mapping"),
                    }
                )

        # Check for data quality issues
        data_quality = asset_data.get("data_quality", {})
        completeness = data_quality.get("completeness_score", 1.0)
        confidence = data_quality.get("confidence_score", 1.0)

        if completeness < 0.7:
            gaps["high"].append(
                {
                    "type": "data_quality",
                    "field": "completeness",
                    "description": f"Low data completeness ({completeness:.1%})",
                    "impact": "May affect migration accuracy",
                }
            )

        if confidence < 0.8:
            gaps["medium"].append(
                {
                    "type": "data_quality",
                    "field": "confidence",
                    "description": f"Low confidence in data ({confidence:.1%})",
                    "impact": "Requires validation",
                }
            )

        # Calculate overall priority score
        priority_score = self._calculate_priority_score(gaps)

        return {
            "asset_id": asset_data.get("asset_id", "unknown"),
            "gaps": gaps,
            "total_gaps": sum(len(gap_list) for gap_list in gaps.values()),
            "priority_score": priority_score,
            "analysis_summary": {
                "critical_issues": len(gaps["critical"]),
                "high_priority": len(gaps["high"]),
                "medium_priority": len(gaps["medium"]),
                "low_priority": len(gaps["low"]),
            },
        }

    def _calculate_priority_score(self, gaps: Dict[str, List]) -> float:
        """Calculate priority score based on gap severity."""
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        score = sum(len(gaps[level]) * weight for level, weight in weights.items())
        return min(100, score * 2)  # Normalize to 0-100
