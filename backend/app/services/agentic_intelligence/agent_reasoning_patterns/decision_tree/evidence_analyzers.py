"""
Evidence Analyzers Module

This module contains all evidence analysis methods that extract insights
from asset data for reasoning purposes.
"""

import logging
from typing import Any, Dict, List

from ..base import ReasoningEvidence, EvidenceType

logger = logging.getLogger(__name__)


class EvidenceAnalyzers:
    """
    Collection of evidence analysis methods for different types of asset data.
    """

    def __init__(self, performance_pattern=None):
        self.performance_pattern = performance_pattern
        self.logger = logger

    async def analyze_technology_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Delegate to business value pattern for technology evidence analysis"""
        return await self.analyze_basic_evidence(
            asset_data, "technology", ["oracle", "sap", "mainframe"]
        )

    async def analyze_usage_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Delegate to performance pattern for usage evidence analysis"""
        if self.performance_pattern:
            return await self.performance_pattern.analyze_performance_trends(asset_data)
        return []

    async def analyze_naming_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Analyze naming patterns for business value clues"""
        evidence = []
        name = asset_data.get("name", "").lower()
        critical_keywords = ["prod", "customer", "financial", "billing", "core"]
        for keyword in critical_keywords:
            if keyword in name:
                evidence.append(
                    ReasoningEvidence(
                        evidence_type=EvidenceType.NAMING_CONVENTIONS,
                        field_name="name",
                        field_value=keyword,
                        confidence=0.6,
                        reasoning=f"Name contains '{keyword}' suggesting business-critical functionality",
                        supporting_patterns=[],
                    )
                )
        return evidence

    async def analyze_environment_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Analyze environment context for business value"""
        evidence = []
        environment = asset_data.get("environment", "").lower()
        if environment in ["production", "prod"]:
            evidence.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.ENVIRONMENT_CONTEXT,
                    field_name="environment",
                    field_value=environment,
                    confidence=0.9,
                    reasoning="Production environment indicates live business operations",
                    supporting_patterns=[],
                )
            )
        return evidence

    async def analyze_technology_risk_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Delegate to risk pattern for technology risk analysis"""
        return await self.analyze_basic_evidence(
            asset_data, "risk", ["java 8", "windows server 2012"]
        )

    async def analyze_security_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Placeholder for security evidence analysis"""
        return []

    async def analyze_compliance_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Placeholder for compliance evidence analysis"""
        return []

    async def analyze_architecture_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Delegate to modernization pattern for architecture analysis"""
        return await self.analyze_basic_evidence(
            asset_data, "architecture", ["microservices", "kubernetes"]
        )

    async def analyze_cloud_readiness_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Analyze cloud readiness indicators"""
        evidence = []
        asset_type = asset_data.get("asset_type", "").lower()
        if "api" in asset_type or "service" in asset_type:
            evidence.append(
                ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="asset_type",
                    field_value=asset_type,
                    confidence=0.7,
                    reasoning="Stateless services are ideal for cloud deployment",
                    supporting_patterns=[],
                )
            )
        return evidence

    async def analyze_technology_modernization_evidence(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """Placeholder for technology modernization analysis"""
        return []

    async def analyze_basic_evidence(
        self, asset_data: Dict[str, Any], category: str, indicators: List[str]
    ) -> List[ReasoningEvidence]:
        """Generic evidence analysis helper"""
        evidence = []
        tech_stack = asset_data.get("technology_stack", "").lower()
        for indicator in indicators:
            if indicator in tech_stack:
                evidence.append(
                    ReasoningEvidence(
                        evidence_type=EvidenceType.TECHNOLOGY_STACK,
                        field_name="technology_stack",
                        field_value=indicator,
                        confidence=0.7,
                        reasoning=f"{category.title()} indicator: {indicator}",
                        supporting_patterns=[],
                    )
                )
        return evidence
