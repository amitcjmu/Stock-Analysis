"""
Utility Functions Module

This module contains utility functions for the reasoning engine including
score conversions and recommendation generators.
"""

import logging
from typing import Any, Dict, List

from ..base import ReasoningEvidence

logger = logging.getLogger(__name__)


class ReasoningUtilities:
    """
    Utility functions for reasoning engine operations.
    """

    @staticmethod
    def risk_level_to_score(risk_level: str) -> int:
        """Convert risk level to numeric score"""
        risk_mapping = {"low": 1, "medium": 5, "high": 8, "critical": 10}
        return risk_mapping.get(risk_level, 5)

    @staticmethod
    def generate_business_value_recommendations(
        asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], score: int
    ) -> List[str]:
        """Generate recommendations based on business value analysis"""
        if score >= 8:
            return [
                "High business value asset - prioritize for migration and ensure minimal downtime",
                "Consider implementing redundancy and backup strategies",
            ]
        elif score >= 6:
            return [
                "Medium-high business value - plan careful migration with testing phases"
            ]
        return [
            "Lower business impact - suitable for experimental migration approaches"
        ]

    @staticmethod
    def generate_risk_recommendations(
        asset_data: Dict[str, Any],
        evidence: List[ReasoningEvidence],
        risk_level: str,
    ) -> List[str]:
        """Generate recommendations based on risk analysis"""
        if risk_level == "high":
            return [
                "High risk asset - prioritize security updates and migration",
                "Implement additional monitoring and security controls",
            ]
        elif risk_level == "medium":
            return [
                "Medium risk - plan migration to address security and compliance concerns"
            ]
        return ["Low risk asset - standard migration approach appropriate"]

    @staticmethod
    def generate_modernization_recommendations(
        asset_data: Dict[str, Any], evidence: List[ReasoningEvidence], score: int
    ) -> List[str]:
        """Generate recommendations based on modernization analysis"""
        if score >= 80:
            return [
                "Excellent modernization candidate - consider containerization and cloud-native patterns",
                "Suitable for microservices architecture and DevOps practices",
            ]
        elif score >= 60:
            return [
                "Good modernization potential - plan phased approach to cloud adoption"
            ]
        return ["Limited modernization potential - consider lift-and-shift approach"]
