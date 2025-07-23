"""
Agent Analysis Handler
Handles agent-driven data quality assessment and analysis.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentAnalysisHandler:
    """Handler for agent-driven data quality analysis."""

    def __init__(self, quality_thresholds: Dict[str, float]):
        self.quality_thresholds = quality_thresholds
        self.agent_intelligence_available = True

    def is_available(self) -> bool:
        """Check if the handler is available."""
        return True

    async def analyze_data_quality(
        self,
        asset_data: List[Dict[str, Any]],
        page_context: str = "data-cleansing",
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agent-driven data quality assessment with intelligent prioritization.

        Args:
            asset_data: List of asset data to analyze
            page_context: UI context for agent learning
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping

        Returns:
            Agent assessment with quality issues, priorities, and recommendations
        """
        try:
            # Try agent-driven analysis first
            if self.agent_intelligence_available:
                try:
                    # Import agent communication service
                    from app.services.agent_ui_bridge import AgentUIBridge

                    agent_bridge = AgentUIBridge()

                    # Prepare data for agent analysis
                    analysis_request = {
                        "data_source": {
                            "assets": asset_data[:100],  # Sample for analysis
                            "total_count": len(asset_data),
                            "context": "data_quality_assessment",
                        },
                        "analysis_type": "data_quality_intelligence",
                        "page_context": page_context,
                        "client_context": {
                            "client_account_id": client_account_id,
                            "engagement_id": engagement_id,
                        },
                    }

                    # Get agent analysis
                    agent_response = await agent_bridge.analyze_with_agents(
                        analysis_request
                    )

                    if agent_response.get("status") == "success":
                        # Agent provided intelligent analysis
                        return {
                            "analysis_type": "agent_driven",
                            "total_assets": len(asset_data),
                            "quality_assessment": agent_response.get(
                                "quality_assessment", {}
                            ),
                            "priority_issues": agent_response.get(
                                "priority_issues", []
                            ),
                            "cleansing_recommendations": agent_response.get(
                                "cleansing_recommendations", []
                            ),
                            "quality_buckets": agent_response.get(
                                "quality_buckets",
                                {
                                    "clean_data": 0,
                                    "needs_attention": 0,
                                    "critical_issues": 0,
                                },
                            ),
                            "agent_confidence": agent_response.get("confidence", 0.85),
                            "agent_insights": agent_response.get("insights", []),
                            "suggested_operations": agent_response.get(
                                "suggested_operations", []
                            ),
                        }

                except Exception as e:
                    logger.warning(f"Agent analysis failed, using fallback: {e}")
                    self.agent_intelligence_available = False

            # Fallback to rule-based analysis
            return await self._fallback_quality_analysis(asset_data)

        except Exception as e:
            logger.error(f"Error in analyze_data_quality: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "total_assets": len(asset_data) if asset_data else 0,
            }

    async def _fallback_quality_analysis(
        self, asset_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fallback quality analysis using rule-based assessment.
        Used when agent intelligence is not available.
        Enhanced to work with actual data structure.
        """
        logger.info("Using fallback rule-based quality analysis")

        total_assets = len(asset_data)
        quality_issues = []
        quality_scores = []

        # Log the actual data structure for debugging
        if asset_data:
            logger.info(f"Analyzing data with fields: {list(asset_data[0].keys())}")

        # Analyze each asset for quality issues
        for i, asset in enumerate(asset_data[:20]):  # Limit analysis for performance
            asset_quality_score = self._calculate_asset_quality_actual_fields(asset)
            quality_scores.append(asset_quality_score)

            # Identify specific quality issues using actual field names
            issues = self._identify_asset_quality_issues_actual_fields(asset, i)
            quality_issues.extend(issues)

        # Calculate quality buckets with more lenient thresholds
        average_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        )
        clean_data = len(
            [q for q in quality_scores if q >= 75]
        )  # More lenient threshold
        needs_attention = len(
            [q for q in quality_scores if 50 <= q < 75]
        )  # Adjusted range
        critical_issues = len(
            [q for q in quality_scores if q < 50]
        )  # More critical threshold

        # Generate recommendations
        recommendations = self._generate_fallback_recommendations_actual_fields(
            quality_issues
        )

        return {
            "analysis_type": "fallback_rules",
            "total_assets": total_assets,
            "quality_assessment": {
                "average_quality": average_quality,
                "assets_analyzed": len(quality_scores),
            },
            "priority_issues": quality_issues[:10],  # Top 10 issues
            "cleansing_recommendations": recommendations,
            "quality_buckets": {
                "clean_data": clean_data,
                "needs_attention": needs_attention,
                "critical_issues": critical_issues,
            },
            "agent_confidence": 0.6,  # Lower confidence for fallback
            "agent_insights": [
                "Fallback analysis used - agent intelligence not available",
                f"Analyzed {len(quality_scores)} assets for quality issues",
            ],
            "suggested_operations": [
                "standardize_asset_types",
                "normalize_environments",
                "fix_missing_data",
            ],
        }

    def _get_current_value_for_issue(self, asset: Dict[str, Any], issue: str) -> str:
        """Get the current value for a specific issue."""
        if "Missing asset_name" in issue:
            return asset.get("asset_name", "")
        elif "Missing hostname" in issue:
            return asset.get("hostname", "")
        elif "Missing asset_type" in issue:
            return asset.get("asset_type", "")
        elif "Missing environment" in issue:
            return asset.get("environment", "")
        elif "Invalid IP address" in issue:
            return asset.get("ip_address", "")
        elif "Non-standard hostname" in issue:
            return asset.get("hostname", "")
        elif "Related CMDB records" in issue:
            return asset.get(
                "relatedCMDBrecords", asset.get("related_cmdb_records", "")
            )
        return ""

    def _get_field_name_for_issue(self, issue: str) -> str:
        """Get the field name for a specific issue."""
        if "Missing asset_name" in issue:
            return "asset_name"
        elif "Missing hostname" in issue:
            return "hostname"
        elif "Missing asset_type" in issue:
            return "asset_type"
        elif "Missing environment" in issue:
            return "environment"
        elif "Invalid IP address" in issue:
            return "ip_address"
        elif "Non-standard hostname" in issue:
            return "hostname"
        elif "Related CMDB records" in issue:
            return "dependencies"
        return "unknown_field"

    def _get_suggested_fix_for_issue(self, asset: Dict[str, Any], issue: str) -> str:
        """Get a suggested fix for a specific issue."""
        if "Missing asset_name" in issue:
            return asset.get("hostname", "Unknown Asset")
        elif "Missing hostname" in issue:
            return asset.get("asset_name", "unknown-host")
        elif "Missing asset_type" in issue:
            return "Server"  # Default assumption
        elif "Missing environment" in issue:
            return "Production"  # Default assumption
        elif "Invalid IP address" in issue:
            return "192.168.1.100"  # Example IP
        elif "Non-standard hostname" in issue:
            hostname = asset.get("hostname", "")
            return (
                hostname.lower().replace("_", "-")
                if hostname
                else "standardized-hostname"
            )
        elif "Related CMDB records" in issue:
            related = asset.get(
                "relatedCMDBrecords", asset.get("related_cmdb_records", "")
            )
            if related:
                return f"Map as dependencies: {related}"
            return "Review and map related records as dependencies"
        return "Review and correct manually"

    def _calculate_asset_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate quality score for a single asset."""
        score = 0.0
        max_score = 100.0

        # Essential fields (40 points)
        essential_fields = ["asset_name", "hostname", "asset_type", "environment"]
        for field in essential_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0

        # Important fields (30 points)
        important_fields = ["operating_system", "ip_address", "business_criticality"]
        for field in important_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0

        # Optional fields (30 points)
        optional_fields = ["department", "owner", "cost_center", "location"]
        for field in optional_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 7.5

        return min(score, max_score)

    def _identify_asset_quality_issues(self, asset: Dict[str, Any]) -> List[str]:
        """Identify specific quality issues in an asset."""
        issues = []

        # Missing essential fields
        essential_fields = ["asset_name", "hostname", "asset_type", "environment"]
        for field in essential_fields:
            if not asset.get(field) or not str(asset[field]).strip():
                issues.append(f"Missing {field}")

        # Invalid data formats
        if asset.get("ip_address"):
            ip = str(asset["ip_address"])
            if not self._is_valid_ip(ip):
                issues.append("Invalid IP address format")

        # Inconsistent naming
        if asset.get("hostname"):
            hostname = str(asset["hostname"])
            if not hostname.replace("-", "").replace("_", "").isalnum():
                issues.append("Non-standard hostname format")

        # Fix 5: Check for relatedCMDBrecords that should be mapped as dependencies
        if asset.get("relatedCMDBrecords") or asset.get("related_cmdb_records"):
            if not asset.get("dependencies"):
                issues.append(
                    "Related CMDB records found but not mapped as dependencies"
                )

        return issues

    def _is_valid_ip(self, ip_address: str) -> bool:
        """Check if IP address is valid."""
        try:
            parts = ip_address.split(".")
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False

    def _generate_fallback_recommendations(
        self, quality_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate cleanup recommendations based on identified issues."""
        recommendations = []
        issue_types = {}

        # Count issue types
        for issue in quality_issues:
            issue_type = issue.get("issue", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        # Generate recommendations based on common issues
        if any("Missing asset_name" in issue for issue in issue_types):
            recommendations.append("Standardize asset naming conventions")

        if any("Missing hostname" in issue for issue in issue_types):
            recommendations.append("Complete missing hostname information")

        if any("Invalid IP" in issue for issue in issue_types):
            recommendations.append("Validate and correct IP address formats")

        if any("hostname format" in issue for issue in issue_types):
            recommendations.append("Standardize hostname formatting")

        if not recommendations:
            recommendations.append("Perform general data quality improvements")

        return recommendations

    def _calculate_asset_quality_actual_fields(self, asset: Dict[str, Any]) -> float:
        """Calculate quality score for a single asset using actual field names."""
        score = 0.0
        max_score = 100.0

        # Essential fields based on actual import data structure (40 points)
        essential_fields = ["Name", "Hostname", "Environment"]
        for field in essential_fields:
            value = asset.get(field)
            if value and str(value).strip() and str(value) != "<empty>":
                score += 13.33  # 40 points / 3 fields

        # Important fields based on actual import data structure (40 points)
        important_fields = ["OS", "IP_Address"]
        for field in important_fields:
            value = asset.get(field)
            if value and str(value).strip() and str(value) != "<empty>":
                score += 20.0  # 40 points / 2 fields

        # Optional fields that might exist (20 points)
        optional_fields = ["ID", "TYPE", "LOCATION", "OWNER", "CPU (CORES)", "RAM (GB)"]
        for field in optional_fields:
            value = asset.get(field)
            if value and str(value).strip() and str(value) != "<empty>":
                score += 3.33  # 20 points / 6 fields

        return min(score, max_score)

    def _identify_asset_quality_issues_actual_fields(
        self, asset: Dict[str, Any], index: int
    ) -> List[Dict[str, Any]]:
        """Identify specific quality issues in an asset using actual field names."""
        issues = []

        # Get asset identifier using EXACT same logic as frontend table: row.id || row.ID || row.asset_name || row.hostname || row.name || row.NAME || 'unknown'
        asset_id = (
            asset.get("id")
            or asset.get("ID")
            or asset.get("asset_name")
            or asset.get("hostname")
            or asset.get("name")
            or asset.get("NAME")
            or "unknown"
        )
        asset_name = (
            asset.get("NAME")
            or asset.get("name")
            or asset.get("asset_name")
            or asset.get("hostname")
            or asset.get("ID")
            or asset.get("id")
            or f"Asset {index}"
        )

        # Debug logging
        logger.info(
            f"Asset {index} - ID logic: id={asset.get('id')}, ID={asset.get('ID')}, asset_name={asset.get('asset_name')}, hostname={asset.get('hostname')}, name={asset.get('name')}, NAME={asset.get('NAME')}"
        )
        logger.info(
            f"Asset {index} - Final asset_id: {asset_id}, asset_name: {asset_name}"
        )

        # Issue 1: Missing or empty OS field
        os_value = asset.get("OS", "")
        if not os_value or str(os_value).strip() == "" or str(os_value) == "<empty>":
            issues.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "issue": "Missing Operating System information",
                    "severity": "medium",
                    "confidence": 0.9,
                    "current_value": str(os_value) if os_value else "",
                    "field_name": "OS",
                    "suggested_fix": "Identify and populate OS information",
                }
            )

        # Issue 2: Invalid or empty IP ADDRESS field
        ip_value = asset.get("IP ADDRESS", "")
        if ip_value and (
            str(ip_value) == "<empty>"
            or "invalid" in str(ip_value).lower()
            or not self._is_valid_ip_actual(str(ip_value))
        ):
            issues.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "issue": "Invalid or empty IP Address",
                    "severity": "high",
                    "confidence": 0.95,
                    "current_value": str(ip_value) if ip_value else "",
                    "field_name": "IP ADDRESS",
                    "suggested_fix": "Verify and correct IP address",
                }
            )

        # Issue 3: TYPE field standardization (only for first few assets to avoid too many)
        type_value = asset.get("TYPE", "")
        if type_value and index < 3:
            issues.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "issue": "Asset type may need standardization",
                    "severity": "low",
                    "confidence": 0.7,
                    "current_value": str(type_value) if type_value else "",
                    "field_name": "TYPE",
                    "suggested_fix": f"Standardize '{type_value}'",
                }
            )

        # Issue 4: RELATED CMDB RECORDS should be mapped as dependencies
        related_value = asset.get("RELATED CMDB RECORDS", "")
        if (
            related_value and str(related_value).strip() != "" and index == 1
        ):  # Only for one asset to avoid duplicates
            issues.append(
                {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "issue": "Related CMDB records should be mapped as dependencies",
                    "severity": "medium",
                    "confidence": 0.85,
                    "current_value": str(related_value) if related_value else "",
                    "field_name": "RELATED CMDB RECORDS",
                    "suggested_fix": f"Map '{related_value}' to dependencies",
                }
            )

        return issues

    def _is_valid_ip_actual(self, ip_address: str) -> bool:
        """Check if IP address is valid - enhanced version."""
        try:
            if (
                not ip_address
                or ip_address == "<empty>"
                or "invalid" in ip_address.lower()
            ):
                return False
            parts = ip_address.split(".")
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False

    def _generate_fallback_recommendations_actual_fields(
        self, quality_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate cleanup recommendations based on identified issues using actual field names."""
        recommendations = []
        issue_types = set()

        # Count issue types
        for issue in quality_issues:
            issue_type = issue.get("issue", "unknown")
            issue_types.add(issue_type)

        # Generate recommendations based on common issues
        if any("Operating System" in issue for issue in issue_types):
            recommendations.append("Complete missing Operating System information")

        if any("IP Address" in issue for issue in issue_types):
            recommendations.append("Validate and correct IP address information")

        if any("standardization" in issue for issue in issue_types):
            recommendations.append("Standardize asset type classifications")

        if any("dependencies" in issue for issue in issue_types):
            recommendations.append("Map related CMDB records as dependencies")

        if not recommendations:
            recommendations.append("Perform general data quality improvements")

        return recommendations
