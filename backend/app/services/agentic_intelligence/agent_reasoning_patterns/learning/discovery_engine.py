"""
Pattern Discovery Engine Module

This module implements pattern discovery functionality that enables agents to
discover new reasoning patterns from asset analysis and user feedback.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from ..base import ReasoningEvidence, EvidenceType
from ..exceptions import PatternDiscoveryError

logger = logging.getLogger(__name__)


class PatternDiscoveryEngine:
    """
    Engine for discovering new reasoning patterns from asset analysis and user feedback.
    """

    def __init__(
        self, memory_manager, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger

    async def discover_business_value_patterns(
        self,
        asset_data: Dict[str, Any],
        evidence: List[ReasoningEvidence],
        agent_name: str,
    ) -> List[Dict[str, Any]]:
        """Discover new business value patterns during analysis"""
        patterns = []

        try:
            # Example: If we see high CPU + production + database, discover pattern
            has_high_cpu = any(
                e.field_name == "cpu_utilization_percent" and e.field_value >= 70
                for e in evidence
            )
            has_production = any(e.field_value == "production" for e in evidence)
            is_database = asset_data.get("asset_type", "").lower() == "database"

            if has_high_cpu and has_production and is_database:
                pattern = {
                    "pattern_type": "business_value_indicator",
                    "pattern_name": "High-Usage Production Database Pattern",
                    "pattern_description": (
                        "Production databases with high CPU utilization indicate "
                        "critical business systems"
                    ),
                    "pattern_logic": {
                        "environment": "production",
                        "asset_type": "database",
                        "cpu_utilization_percent": {"operator": ">=", "value": 70},
                    },
                    "confidence_score": 0.85,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
                patterns.append(pattern)

            # Financial system pattern discovery
            patterns.extend(self._discover_financial_patterns(asset_data, agent_name))

        except Exception as e:
            self.logger.error(f"Error discovering business value patterns: {e}")
            raise PatternDiscoveryError(
                f"Failed to discover business value patterns: {e}",
                discovery_context={
                    "agent": agent_name,
                    "asset_id": asset_data.get("id"),
                },
            )

        return patterns

    def _discover_financial_patterns(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> List[Dict[str, Any]]:
        """Helper to discover financial system patterns"""
        patterns = []
        name = asset_data.get("name", "").lower()
        tech_stack = asset_data.get("technology_stack", "").lower()
        financial_keywords = ["finance", "billing", "payment", "accounting"]
        enterprise_tech = ["oracle", "sap", "peoplesoft"]

        if any(keyword in name for keyword in financial_keywords) and any(
            tech in tech_stack for tech in enterprise_tech
        ):
            patterns.append(
                {
                    "pattern_type": "business_value_indicator",
                    "pattern_name": "Financial Enterprise System Pattern",
                    "pattern_description": "Financial systems using enterprise technology are business-critical",
                    "pattern_logic": {
                        "naming_patterns": financial_keywords,
                        "technology_stack": {"contains_any": enterprise_tech},
                    },
                    "confidence_score": 0.9,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
            )
        return patterns

    async def discover_risk_patterns(
        self,
        asset_data: Dict[str, Any],
        evidence: List[ReasoningEvidence],
        agent_name: str,
    ) -> List[Dict[str, Any]]:
        """Discover new risk patterns during analysis"""
        patterns = []

        try:
            # Check for legacy technology patterns
            patterns.extend(
                self._discover_legacy_risk_patterns(asset_data, evidence, agent_name)
            )

            # Check for unsupported platform patterns
            patterns.extend(
                self._discover_unsupported_platform_patterns(asset_data, agent_name)
            )

        except Exception as e:
            self.logger.error(f"Error discovering risk patterns: {e}")
            raise PatternDiscoveryError(
                f"Failed to discover risk patterns: {e}",
                discovery_context={
                    "agent": agent_name,
                    "asset_id": asset_data.get("id"),
                },
            )

        return patterns

    def _discover_legacy_risk_patterns(
        self,
        asset_data: Dict[str, Any],
        evidence: List[ReasoningEvidence],
        agent_name: str,
    ) -> List[Dict[str, Any]]:
        """Helper to discover legacy technology risk patterns"""
        patterns = []
        has_legacy_tech = any(
            e.evidence_type == EvidenceType.TECHNOLOGY_STACK
            and any(
                legacy in str(e.field_value)
                for legacy in ["java 8", "windows server 2012"]
            )
            for e in evidence
        )
        is_production = asset_data.get("environment", "").lower() in [
            "production",
            "prod",
        ]

        if has_legacy_tech and is_production:
            patterns.append(
                {
                    "pattern_type": "risk_factor",
                    "pattern_name": "Legacy Technology in Production Risk",
                    "pattern_description": (
                        "Legacy technologies in production environments "
                        "pose significant operational risks"
                    ),
                    "pattern_logic": {
                        "environment": "production",
                        "technology_stack": {
                            "contains_any": ["java 8", "windows server 2012"]
                        },
                    },
                    "confidence_score": 0.8,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
            )
        return patterns

    def _discover_unsupported_platform_patterns(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> List[Dict[str, Any]]:
        """Helper to discover unsupported platform risk patterns"""
        patterns = []
        tech_stack = asset_data.get("technology_stack", "").lower()
        unsupported_platforms = ["centos 6", "ubuntu 14", "windows server 2008"]
        is_production = asset_data.get("environment", "").lower() in [
            "production",
            "prod",
        ]

        if (
            any(platform in tech_stack for platform in unsupported_platforms)
            and is_production
        ):
            patterns.append(
                {
                    "pattern_type": "risk_factor",
                    "pattern_name": "Unsupported Platform in Production Risk",
                    "pattern_description": (
                        "Unsupported platforms in production create critical "
                        "security and compliance risks"
                    ),
                    "pattern_logic": {
                        "environment": "production",
                        "technology_stack": {"contains_any": unsupported_platforms},
                    },
                    "confidence_score": 0.9,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
            )
        return patterns

    async def discover_modernization_patterns(
        self,
        asset_data: Dict[str, Any],
        evidence: List[ReasoningEvidence],
        agent_name: str,
    ) -> List[Dict[str, Any]]:
        """Discover new modernization patterns during analysis"""
        patterns = []

        try:
            # Example: Spring Boot + API = high modernization potential
            tech_stack = asset_data.get("technology_stack", "").lower()
            asset_type = asset_data.get("asset_type", "").lower()

            if "spring boot" in tech_stack and "api" in asset_type:
                pattern = {
                    "pattern_type": "modernization_opportunity",
                    "pattern_name": "Spring Boot API Modernization Ready",
                    "pattern_description": (
                        "Spring Boot APIs are excellent candidates for containerization "
                        "and cloud migration"
                    ),
                    "pattern_logic": {
                        "technology_stack": {"contains": "spring boot"},
                        "asset_type": {"contains": "api"},
                    },
                    "confidence_score": 0.9,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
                patterns.append(pattern)

            # Microservices architecture pattern
            if "microservices" in tech_stack or "kubernetes" in tech_stack:
                pattern = {
                    "pattern_type": "modernization_opportunity",
                    "pattern_name": "Cloud-Native Architecture Ready",
                    "pattern_description": (
                        "Assets with microservices or Kubernetes are ready for "
                        "cloud-native modernization"
                    ),
                    "pattern_logic": {
                        "technology_stack": {
                            "contains_any": ["microservices", "kubernetes", "docker"]
                        },
                    },
                    "confidence_score": 0.85,
                    "evidence_assets": (
                        [asset_data.get("id")] if asset_data.get("id") else []
                    ),
                    "discovered_by": agent_name,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                }
                patterns.append(pattern)

        except Exception as e:
            self.logger.error(f"Error discovering modernization patterns: {e}")
            raise PatternDiscoveryError(
                f"Failed to discover modernization patterns: {e}",
                discovery_context={
                    "agent": agent_name,
                    "asset_id": asset_data.get("id"),
                },
            )

        return patterns
