"""
File type analysis and content detection for data import validation.
Provides intelligent file type detection and recommended agent routing.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """Analyzes file type and content for intelligent routing"""

    def __init__(self, state):
        self.state = state

    def analyze_file_type_and_content(self) -> Dict[str, Any]:
        """
        Analyze the imported data to determine file type and recommend appropriate agents.
        Uses pattern recognition similar to agent intelligence for routing decisions.
        """
        try:
            if not self.state.raw_data or not isinstance(self.state.raw_data[0], dict):
                return {
                    "detected_type": "unknown",
                    "confidence": 0.0,
                    "recommended_agent": "CMDB_Data_Analyst_Agent",
                    "analysis_details": {"error": "No valid data to analyze"},
                }

            # Get field names and sample data for analysis
            first_record = self.state.raw_data[0]
            field_names = list(first_record.keys())
            field_names_lower = [name.lower() for name in field_names]

            # Analyze patterns to determine file type (agent-like pattern recognition)
            type_indicators = self._get_type_indicators()
            type_scores = {}

            for data_type, indicators in type_indicators.items():
                field_matches = []
                pattern_matches = []

                # Check field name matches
                for indicator in indicators["field_patterns"]:
                    for field in field_names_lower:
                        if indicator in field:
                            field_matches.append((indicator, field))

                # Check value pattern matches (sample first record)
                for pattern_key, pattern_values in indicators.get(
                    "value_patterns", {}
                ).items():
                    for field_name, field_value in first_record.items():
                        if isinstance(field_value, str) and any(
                            pattern in field_value.lower() for pattern in pattern_values
                        ):
                            pattern_matches.append((pattern_key, field_name))

                # Calculate score as percentage of fields that match indicators
                total_indicators = len(indicators["field_patterns"])
                match_score = len(field_matches) / max(total_indicators, 1)

                # Boost score for value pattern matches
                if pattern_matches:
                    match_score += 0.2  # 20% boost for value patterns

                type_scores[data_type] = min(match_score, 1.0)  # Cap at 100%

            # Determine the best match (agent-like decision making)
            best_type = (
                max(type_scores, key=type_scores.get) if type_scores else "unknown"
            )
            best_score = type_scores.get(best_type, 0.0)

            # Map to recommended agents (agent-like expertise routing)
            agent_mapping = {
                "server_inventory": "Server_Classification_Expert",
                "application_inventory": "Application_Discovery_Expert",
                "network_inventory": "Network_Infrastructure_Expert",
                "security_inventory": "Security_Asset_Expert",
                "monitoring_data": "Performance_Monitoring_Expert",
                "cmdb_export": "CMDB_Data_Analyst_Agent",
                "asset_management": "IT_Asset_Inventory_Manager",
            }

            # If no clear type detected, default to CMDB for asset-like data
            if best_score < 0.3:
                best_type = "cmdb_export"
                best_score = 0.5  # Default moderate confidence

            recommended_agent = agent_mapping.get(best_type, "CMDB_Data_Analyst_Agent")

            # Generate analysis details (agent-like reporting)
            analysis_details = {
                "field_count": len(field_names),
                "record_count": len(self.state.raw_data),
                "type_scores": type_scores,
                "field_analysis": {
                    "total_fields": len(field_names),
                    "sample_fields": field_names[:10],  # First 10 fields
                },
                "detection_confidence": best_score,
                "alternative_types": [
                    {"type": t, "score": s}
                    for t, s in sorted(
                        type_scores.items(), key=lambda x: x[1], reverse=True
                    )[:3]
                ],
            }

            logger.info(f"🔍 File analysis: {best_type} (confidence: {best_score:.2%})")

            return {
                "detected_type": best_type,
                "confidence": best_score,
                "recommended_agent": recommended_agent,
                "analysis_details": analysis_details,
            }

        except Exception as e:
            logger.error(f"❌ File analysis failed: {str(e)}", exc_info=True)
            return {
                "detected_type": "unknown",
                "confidence": 0.0,
                "recommended_agent": "CMDB_Data_Analyst_Agent",
                "analysis_details": {"error": str(e)},
            }

    def _get_type_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Get field patterns for different data types (agent knowledge patterns)"""
        return {
            "server_inventory": {
                "field_patterns": [
                    "server",
                    "host",
                    "hostname",
                    "ip",
                    "cpu",
                    "memory",
                    "ram",
                    "disk",
                    "storage",
                    "os",
                    "operating",
                    "kernel",
                    "uptime",
                    "hardware",
                ],
                "value_patterns": {
                    "os_types": ["windows", "linux", "unix", "aix", "solaris"],
                    "server_roles": ["web", "database", "application", "file", "mail"],
                },
            },
            "application_inventory": {
                "field_patterns": [
                    "application",
                    "app",
                    "service",
                    "process",
                    "port",
                    "url",
                    "version",
                    "vendor",
                    "license",
                    "database",
                    "middleware",
                    "runtime",
                ],
                "value_patterns": {
                    "app_types": ["web", "api", "service", "batch", "gui"],
                    "tech_stack": ["java", "python", ".net", "php", "node"],
                },
            },
            "network_inventory": {
                "field_patterns": [
                    "network",
                    "switch",
                    "router",
                    "vlan",
                    "subnet",
                    "gateway",
                    "dns",
                    "dhcp",
                    "firewall",
                    "load_balancer",
                    "proxy",
                ],
                "value_patterns": {
                    "network_types": ["lan", "wan", "vpn", "dmz"],
                    "protocols": ["tcp", "udp", "http", "https", "ssh"],
                },
            },
            "security_inventory": {
                "field_patterns": [
                    "security",
                    "antivirus",
                    "firewall",
                    "certificate",
                    "ssl",
                    "tls",
                    "access",
                    "permission",
                    "role",
                    "user",
                    "group",
                    "policy",
                ],
                "value_patterns": {
                    "security_tools": ["symantec", "mcafee", "kaspersky", "checkpoint"],
                    "access_levels": ["admin", "user", "guest", "service"],
                },
            },
            "monitoring_data": {
                "field_patterns": [
                    "metric",
                    "performance",
                    "cpu_usage",
                    "memory_usage",
                    "disk_usage",
                    "response_time",
                    "throughput",
                    "error_rate",
                    "availability",
                    "sla",
                ],
                "value_patterns": {
                    "metrics": ["percent", "bytes", "seconds", "requests", "errors"],
                    "thresholds": ["critical", "warning", "normal", "baseline"],
                },
            },
            "asset_management": {
                "field_patterns": [
                    "asset",
                    "inventory",
                    "tag",
                    "serial",
                    "model",
                    "manufacturer",
                    "purchase",
                    "warranty",
                    "lifecycle",
                    "status",
                    "location",
                    "owner",
                ],
                "value_patterns": {
                    "manufacturers": ["dell", "hp", "ibm", "cisco", "vmware"],
                    "statuses": ["active", "inactive", "retired", "maintenance"],
                },
            },
            "cmdb_export": {
                "field_patterns": [
                    "ci",
                    "configuration",
                    "item",
                    "class",
                    "category",
                    "relationship",
                    "dependency",
                    "attribute",
                    "name",
                    "type",
                    "environment",
                ],
                "value_patterns": {
                    "ci_types": ["server", "application", "service", "database"],
                    "environments": ["production", "staging", "development", "test"],
                },
            },
        }
