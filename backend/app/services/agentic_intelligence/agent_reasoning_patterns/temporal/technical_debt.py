"""
Technical Debt Accumulation Pattern Module

This module implements temporal reasoning patterns for technical debt accumulation analysis,
tracking how technical debt accumulates over time and impacts modernization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .temporal_core import TemporalPoint

logger = logging.getLogger(__name__)


class TechnicalDebtAccumulationPattern(BaseReasoningPattern):
    """
    Temporal reasoning pattern for technical debt accumulation analysis.
    Tracks how technical debt accumulates over time and impacts modernization.
    """

    def __init__(self):
        super().__init__(
            "technical_debt_temporal",
            "Technical Debt Accumulation Analysis",
            "Analyzes how technical debt accumulates over time",
        )

    def analyze_technical_debt_accumulation(
        self, asset_data: Dict[str, Any], asset_age: TemporalPoint
    ) -> List[ReasoningEvidence]:
        """
        Analyze technical debt accumulation based on asset age and characteristics.

        Args:
            asset_data: Asset data
            asset_age: Asset age information

        Returns:
            List of evidence pieces from technical debt analysis
        """
        evidence_pieces = []
        age_years = asset_age.age_in_years()

        # Calculate debt accumulation based on technology and age
        debt_factors = self._calculate_debt_factors(asset_data, age_years)

        if debt_factors["total_debt_score"] > 0.6:
            evidence_pieces.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNICAL_COMPLEXITY,
                    field_name="technical_debt_accumulation",
                    field_value=debt_factors["total_debt_score"],
                    confidence=0.8,
                    reasoning=(
                        f"High technical debt accumulation "
                        f"({debt_factors['total_debt_score']:.2f}) after {age_years:.1f} years"
                    ),
                    supporting_patterns=[self.pattern_id],
                )
            )

        # Analyze specific debt contributors
        for factor, score in debt_factors["contributing_factors"].items():
            if score > 0.5:
                evidence_pieces.append(
                    ReasoningEvidence(
                        evidence_type=EvidenceType.TECHNICAL_COMPLEXITY,
                        field_name=f"debt_factor_{factor}",
                        field_value=score,
                        confidence=0.7,
                        reasoning=f"Technical debt factor '{factor}' contributes {score:.2f} to overall debt",
                        supporting_patterns=[self.pattern_id],
                    )
                )

        return evidence_pieces

    def _calculate_debt_factors(
        self, asset_data: Dict[str, Any], age_years: float
    ) -> Dict[str, Any]:
        """Calculate various technical debt factors"""
        factors = {
            "age_factor": min(1.0, age_years / 5.0),  # Debt increases with age
            "technology_factor": self._calculate_technology_debt(asset_data),
            "maintenance_factor": self._calculate_maintenance_debt(asset_data),
            "complexity_factor": self._calculate_complexity_debt(asset_data),
        }

        total_debt = sum(factors.values()) / len(factors)

        return {
            "total_debt_score": total_debt,
            "contributing_factors": factors,
        }

    def _calculate_technology_debt(self, asset_data: Dict[str, Any]) -> float:
        """Calculate debt from technology choices"""
        tech_stack = asset_data.get("technology_stack", "").lower()
        legacy_penalties = {
            "java 8": 0.3,
            "windows server 2012": 0.4,
            "oracle 11g": 0.3,
            ".net framework": 0.2,
            "php 5": 0.4,
        }
        return min(
            1.0,
            sum(
                penalty
                for tech, penalty in legacy_penalties.items()
                if tech in tech_stack
            ),
        )

    def _calculate_maintenance_debt(self, asset_data: Dict[str, Any]) -> float:
        """Calculate debt from maintenance patterns"""
        last_updated = asset_data.get("last_updated")
        if last_updated:
            try:
                last_update = datetime.fromisoformat(
                    last_updated.replace("Z", "+00:00")
                )
                return min(1.0, (datetime.utcnow() - last_update).days / 365.0)
            except (ValueError, TypeError):
                pass
        return 0.5

    def _calculate_complexity_debt(self, asset_data: Dict[str, Any]) -> float:
        """Calculate debt from complexity indicators"""
        complexity_score = 0.0
        if "monolith" in asset_data.get("architecture_type", "").lower():
            complexity_score += 0.3
        if asset_data.get("lines_of_code", 0) > 100000:
            complexity_score += 0.2
        return min(1.0, complexity_score)
