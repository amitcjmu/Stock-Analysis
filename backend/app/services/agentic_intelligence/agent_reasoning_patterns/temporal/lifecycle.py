"""
Asset Lifecycle Pattern Module

This module implements temporal reasoning patterns for asset lifecycle analysis,
evaluating assets based on their age, lifecycle stage, and temporal characteristics.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .temporal_core import TemporalPoint

logger = logging.getLogger(__name__)


class AssetLifecyclePattern(BaseReasoningPattern):
    """
    Temporal reasoning pattern for asset lifecycle analysis.
    Evaluates assets based on their age, lifecycle stage, and temporal characteristics.
    """

    def __init__(self):
        super().__init__(
            "asset_lifecycle",
            "Asset Lifecycle Analysis",
            "Analyzes assets based on lifecycle stage and temporal factors",
        )
        self.lifecycle_stages = self._initialize_lifecycle_stages()

    def _initialize_lifecycle_stages(self) -> Dict[str, Dict[str, Any]]:
        """Initialize lifecycle stage definitions"""
        return {
            "new": {
                "age_range_months": (0, 6),
                "risk_factor": 0.3,
                "business_value_modifier": 0.8,
                "modernization_potential": 0.9,
                "description": "Recently deployed or updated asset",
            },
            "mature": {
                "age_range_months": (6, 36),
                "risk_factor": 0.2,
                "business_value_modifier": 1.0,
                "modernization_potential": 0.7,
                "description": "Stable, well-established asset in production",
            },
            "aging": {
                "age_range_months": (36, 72),
                "risk_factor": 0.5,
                "business_value_modifier": 0.9,
                "modernization_potential": 0.5,
                "description": "Aging asset requiring attention and updates",
            },
            "legacy": {
                "age_range_months": (72, 120),
                "risk_factor": 0.7,
                "business_value_modifier": 0.8,
                "modernization_potential": 0.3,
                "description": "Legacy asset with increasing maintenance burden",
            },
            "obsolete": {
                "age_range_months": (120, float("inf")),
                "risk_factor": 0.9,
                "business_value_modifier": 0.6,
                "modernization_potential": 0.1,
                "description": "Obsolete asset requiring urgent replacement",
            },
        }

    def analyze_asset_lifecycle(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """
        Analyze asset lifecycle stage and temporal factors.

        Args:
            asset_data: Asset data including creation/update timestamps

        Returns:
            List of evidence pieces from lifecycle analysis
        """
        evidence_pieces = []

        # Determine asset age
        asset_age = self._calculate_asset_age(asset_data)
        if asset_age is None:
            return evidence_pieces

        # Determine lifecycle stage
        lifecycle_stage = self._determine_lifecycle_stage(asset_age)
        stage_info = self.lifecycle_stages[lifecycle_stage]

        # Create lifecycle evidence
        evidence_pieces.append(
            ReasoningEvidence(
                evidence_type=EvidenceType.ENVIRONMENT_CONTEXT,
                field_name="lifecycle_stage",
                field_value=lifecycle_stage,
                confidence=0.9,
                reasoning=(
                    f"Asset is {asset_age.age_in_months()} months old, "
                    f"categorized as {lifecycle_stage}: {stage_info['description']}"
                ),
                supporting_patterns=[self.pattern_id],
            )
        )

        # Risk assessment based on age
        if lifecycle_stage in ["aging", "legacy", "obsolete"]:
            evidence_pieces.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="age_related_risk",
                    field_value=stage_info["risk_factor"],
                    confidence=0.8,
                    reasoning=(
                        f"Asset age ({asset_age.age_in_months()} months) "
                        f"indicates {lifecycle_stage} stage with elevated risk"
                    ),
                    supporting_patterns=[self.pattern_id],
                )
            )

        # Technology obsolescence analysis
        tech_obsolescence = self._analyze_technology_obsolescence(asset_data, asset_age)
        if tech_obsolescence:
            evidence_pieces.extend(tech_obsolescence)

        return evidence_pieces

    def _calculate_asset_age(
        self, asset_data: Dict[str, Any]
    ) -> Optional[TemporalPoint]:
        """Calculate asset age from available timestamps"""
        # Try different timestamp fields
        timestamp_fields = [
            "created_at",
            "last_updated",
            "deployment_date",
            "created_date",
        ]

        for field in timestamp_fields:
            timestamp_value = asset_data.get(field)
            if timestamp_value:
                try:
                    if isinstance(timestamp_value, str):
                        # Try to parse ISO format
                        timestamp = datetime.fromisoformat(
                            timestamp_value.replace("Z", "+00:00")
                        )
                    elif isinstance(timestamp_value, datetime):
                        timestamp = timestamp_value
                    else:
                        continue

                    return TemporalPoint(timestamp, field, {"source_field": field})
                except (ValueError, TypeError):
                    continue

        return None

    def _determine_lifecycle_stage(self, asset_age: TemporalPoint) -> str:
        """Determine lifecycle stage based on asset age"""
        age_months = asset_age.age_in_months()

        for stage, stage_info in self.lifecycle_stages.items():
            min_age, max_age = stage_info["age_range_months"]
            if min_age <= age_months < max_age:
                return stage

        return "obsolete"  # Default for very old assets

    def _analyze_technology_obsolescence(
        self, asset_data: Dict[str, Any], asset_age: TemporalPoint
    ) -> List[ReasoningEvidence]:
        """Analyze technology obsolescence based on age and stack"""
        evidence_pieces = []
        tech_stack = asset_data.get("technology_stack", "").lower()

        # Technology obsolescence patterns
        obsolescence_patterns = {
            "java 8": {"obsolete_after_months": 60, "risk_multiplier": 1.5},
            "windows server 2012": {
                "obsolete_after_months": 48,
                "risk_multiplier": 2.0,
            },
            "centos 6": {"obsolete_after_months": 36, "risk_multiplier": 2.5},
            "ubuntu 14": {"obsolete_after_months": 48, "risk_multiplier": 2.0},
            ".net framework 4": {"obsolete_after_months": 72, "risk_multiplier": 1.3},
        }

        for tech, pattern in obsolescence_patterns.items():
            if tech in tech_stack:
                age_months = asset_age.age_in_months()
                if age_months >= pattern["obsolete_after_months"]:
                    evidence_pieces.append(
                        ReasoningEvidence(
                            evidence_type=EvidenceType.TECHNOLOGY_STACK,
                            field_name="technology_obsolescence",
                            field_value=tech,
                            confidence=0.9,
                            reasoning=(
                                f"Technology {tech} is obsolete after {age_months} months "
                                f"(threshold: {pattern['obsolete_after_months']})"
                            ),
                            supporting_patterns=[self.pattern_id],
                        )
                    )

        return evidence_pieces
