"""
Dependency Analysis Tools - Tool Classes and Result Models

This module contains the tool classes used by the Dependency Analysis Crew
for network topology analysis and dependency mapping.

Tools:
1. NetworkTopologyTool - Analyzes network topology and architecture patterns
2. DependencyAnalysisResult - Pydantic model for structured dependency results
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from crewai.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DependencyAnalysisResult(BaseModel):
    """Result model for dependency analysis"""

    asset_id: str
    asset_name: str
    network_analysis: Dict[str, Any]
    application_dependencies: Dict[str, Any]
    infrastructure_dependencies: Dict[str, Any]
    critical_path_analysis: Dict[str, Any]
    dependency_map: Dict[str, Any]
    migration_sequence: List[str]
    risk_assessment: Dict[str, Any]
    confidence_score: float


class NetworkTopologyTool(BaseTool):
    """Tool for network topology analysis and architecture assessment"""

    name: str = "network_topology_tool"
    description: str = (
        "Analyze network topology and architecture patterns for dependency mapping"
    )

    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network topology and connections"""
        try:
            # Network connection patterns
            network_indicators = {
                "ip_addresses": [],
                "ports": [],
                "protocols": [],
                "network_segments": [],
                "connection_patterns": [],
            }

            # Extract network information from asset data
            asset_text = " ".join(
                str(value).lower() for value in asset_data.values() if value
            )

            # Port detection
            port_keywords = [
                "port",
                "tcp",
                "udp",
                "http",
                "https",
                "ssh",
                "ftp",
                "smtp",
            ]
            for keyword in port_keywords:
                if keyword in asset_text:
                    network_indicators["ports"].append(keyword)

            # Protocol detection
            protocol_keywords = [
                "http",
                "https",
                "tcp",
                "udp",
                "ssh",
                "ftp",
                "smtp",
                "dns",
                "dhcp",
            ]
            for protocol in protocol_keywords:
                if protocol in asset_text:
                    network_indicators["protocols"].append(protocol)

            # Network architecture assessment
            architecture_patterns = {
                "web_tier": ["web", "frontend", "ui", "portal"],
                "application_tier": ["app", "application", "service", "api"],
                "database_tier": ["database", "db", "data", "storage"],
                "integration_tier": ["integration", "middleware", "esb", "queue"],
            }

            tier_analysis = {}
            for tier, keywords in architecture_patterns.items():
                matches = [kw for kw in keywords if kw in asset_text]
                if matches:
                    tier_analysis[tier] = {
                        "identified": True,
                        "indicators": matches,
                        "confidence": len(matches) / len(keywords),
                    }

            # Connection complexity assessment
            complexity_score = 0
            if len(network_indicators["ports"]) > 3:
                complexity_score += 2
            if len(network_indicators["protocols"]) > 2:
                complexity_score += 1
            if len(tier_analysis) > 1:
                complexity_score += 3

            complexity_level = (
                "high"
                if complexity_score >= 6
                else "medium" if complexity_score >= 3 else "low"
            )

            return {
                "network_indicators": network_indicators,
                "tier_analysis": tier_analysis,
                "complexity_level": complexity_level,
                "complexity_score": complexity_score,
                "architecture_type": self._determine_architecture_type(tier_analysis),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Network topology analysis failed: {e}")
            return {
                "network_indicators": {},
                "complexity_level": "unknown",
                "error": str(e),
            }

    def _determine_architecture_type(self, tier_analysis: Dict[str, Any]) -> str:
        """Determine the overall architecture type"""
        identified_tiers = [
            tier for tier, data in tier_analysis.items() if data.get("identified")
        ]

        if len(identified_tiers) >= 3:
            return "multi_tier"
        elif "web_tier" in identified_tiers and "database_tier" in identified_tiers:
            return "web_application"
        elif "application_tier" in identified_tiers:
            return "application_service"
        elif "database_tier" in identified_tiers:
            return "data_service"
        else:
            return "standalone"


# Export tool classes
__all__ = [
    "NetworkTopologyTool",
    "DependencyAnalysisResult",
]
