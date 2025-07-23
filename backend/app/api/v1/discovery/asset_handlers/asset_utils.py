"""
Asset Utils Handler
Handles utility functions, transformations, and helper operations.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AssetUtilsHandler:
    """Handles asset utility functions with graceful fallbacks."""

    def __init__(self):
        self.service_available = True
        logger.info("Asset utilities handler initialized successfully")

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available

    def transform_asset_for_frontend(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform asset data for frontend consumption.
        """
        try:
            transformed = {
                # Core identifiers
                "id": asset.get("id")
                or asset.get("ci_id")
                or asset.get("asset_id", "unknown"),
                "name": asset.get("asset_name")
                or asset.get("hostname", "Unknown Asset"),
                "hostname": asset.get("hostname", ""),
                "ip_address": asset.get("ip_address", ""),
                # Basic info
                "type": asset.get("asset_type", "Unknown"),
                "environment": asset.get("environment", "Unknown"),
                "department": asset.get("department")
                or asset.get("business_owner", "Unknown"),
                "criticality": self.map_criticality(
                    asset.get("status") or asset.get("criticality", "Medium")
                ),
                # Technical details
                "operating_system": asset.get("operating_system", ""),
                "os_family": self.standardize_os_family(
                    asset.get("operating_system", "")
                ),
                "cpu_cores": self.extract_numeric_value(asset.get("cpu_cores")),
                "memory_gb": self.extract_numeric_value(asset.get("memory_gb")),
                "storage_gb": self.extract_numeric_value(asset.get("storage_gb")),
                # Technology and complexity
                "technology_stack": asset.get("technology_stack")
                or self.build_tech_stack_from_asset(asset),
                "complexity_score": asset.get("complexity_score", 5),
                "business_value_score": asset.get("business_value_score", 5),
                # Assessment fields
                "data_sensitivity": asset.get("data_sensitivity", "Medium"),
                "compliance_requirements": asset.get("compliance_requirements", []),
                "technical_debt_level": asset.get("technical_debt_level", "Medium"),
                "modernization_potential": asset.get(
                    "modernization_potential", "Medium"
                ),
                "cloud_readiness": asset.get("cloud_readiness", "Medium"),
                # Metadata
                "tags": asset.get("tags", []),
                "dependencies": asset.get("dependencies", []),
                "last_updated": asset.get("updated_timestamp")
                or asset.get("reprocessed_timestamp", ""),
                "created_timestamp": asset.get("created_timestamp", ""),
                # Additional fields that might be present
                "location": asset.get("location", ""),
                "owner": asset.get("owner", ""),
                "vendor": asset.get("vendor", ""),
                "model": asset.get("model", ""),
                "serial_number": asset.get("serial_number", ""),
                "warranty_date": asset.get("warranty_date", ""),
                "maintenance_window": asset.get("maintenance_window", ""),
                # Discovery metadata
                "discovery_source": asset.get("discovery_source", "manual"),
                "discovery_timestamp": asset.get("discovery_timestamp", ""),
                "confidence_score": asset.get("confidence_score", 0.8),
            }

            return transformed

        except Exception as e:
            logger.warning(f"Error transforming asset for frontend: {e}")
            # Return minimal safe transformation
            return {
                "id": asset.get("id", "unknown"),
                "name": asset.get("asset_name")
                or asset.get("hostname", "Unknown Asset"),
                "type": asset.get("asset_type", "Unknown"),
                "environment": asset.get("environment", "Unknown"),
                "department": asset.get("department", "Unknown"),
                "criticality": "Medium",
                "error": f"Transformation error: {str(e)}",
            }

    def build_tech_stack_from_asset(self, asset: Dict[str, Any]) -> str:
        """Build technology stack string from asset data."""
        try:
            tech_components = []

            # Operating system
            os_name = asset.get("operating_system", "")
            if os_name:
                tech_components.append(self.standardize_os_family(os_name))

            # Try to extract from asset name or description
            asset_name = str(asset.get("asset_name", "")).lower()
            hostname = str(asset.get("hostname", "")).lower()
            combined_text = f"{asset_name} {hostname}"

            # Common technology patterns
            if any(tech in combined_text for tech in ["java", "jvm"]):
                tech_components.append("Java")
            if any(tech in combined_text for tech in ["python", "py"]):
                tech_components.append("Python")
            if any(tech in combined_text for tech in ["node", "nodejs"]):
                tech_components.append("Node.js")
            if any(tech in combined_text for tech in [".net", "dotnet", "csharp"]):
                tech_components.append(".NET")
            if any(tech in combined_text for tech in ["php"]):
                tech_components.append("PHP")
            if any(tech in combined_text for tech in ["ruby", "rails"]):
                tech_components.append("Ruby")

            # Database technologies
            if any(db in combined_text for db in ["mysql", "mariadb"]):
                tech_components.append("MySQL")
            if any(db in combined_text for db in ["postgres", "postgresql"]):
                tech_components.append("PostgreSQL")
            if any(db in combined_text for db in ["oracle", "ora"]):
                tech_components.append("Oracle")
            if any(db in combined_text for db in ["mongo", "mongodb"]):
                tech_components.append("MongoDB")
            if any(db in combined_text for db in ["redis"]):
                tech_components.append("Redis")
            if any(db in combined_text for db in ["elastic", "elasticsearch"]):
                tech_components.append("Elasticsearch")

            # Web servers and frameworks
            if any(web in combined_text for web in ["apache", "httpd"]):
                tech_components.append("Apache")
            if any(web in combined_text for web in ["nginx"]):
                tech_components.append("Nginx")
            if any(web in combined_text for web in ["tomcat"]):
                tech_components.append("Tomcat")
            if any(web in combined_text for web in ["iis"]):
                tech_components.append("IIS")

            # Application servers
            if any(app in combined_text for app in ["websphere", "was"]):
                tech_components.append("WebSphere")
            if any(app in combined_text for app in ["weblogic", "wls"]):
                tech_components.append("WebLogic")
            if any(app in combined_text for app in ["jboss", "wildfly"]):
                tech_components.append("JBoss")

            # Container technologies
            if any(container in combined_text for container in ["docker"]):
                tech_components.append("Docker")
            if any(container in combined_text for container in ["kubernetes", "k8s"]):
                tech_components.append("Kubernetes")

            # Remove duplicates and return
            unique_components = list(dict.fromkeys(tech_components))  # Preserves order
            return ", ".join(unique_components) if unique_components else "Unknown"

        except Exception as e:
            logger.warning(f"Error building tech stack: {e}")
            return "Unknown"

    def map_criticality(self, status: str) -> str:
        """Map various status values to standard criticality levels."""
        try:
            if not status:
                return "Medium"

            status_lower = status.lower().strip()

            # High criticality indicators
            if any(
                indicator in status_lower
                for indicator in [
                    "critical",
                    "high",
                    "production",
                    "prod",
                    "tier1",
                    "tier-1",
                    "mission-critical",
                    "business-critical",
                    "essential",
                    "vital",
                ]
            ):
                return "High"

            # Low criticality indicators
            elif any(
                indicator in status_lower
                for indicator in [
                    "low",
                    "tier3",
                    "tier-3",
                    "non-critical",
                    "optional",
                    "development",
                    "dev",
                    "test",
                    "sandbox",
                ]
            ):
                return "Low"

            # Medium is default
            else:
                return "Medium"

        except Exception:
            return "Medium"

    def standardize_os_family(self, os_name: str) -> str:
        """Standardize operating system family."""
        try:
            if not os_name:
                return "Unknown"

            os_lower = os_name.lower().strip()

            # Windows family
            if any(win in os_lower for win in ["windows", "win", "microsoft"]):
                return "Windows"

            # Linux family
            elif any(
                linux in os_lower
                for linux in [
                    "linux",
                    "ubuntu",
                    "redhat",
                    "rhel",
                    "centos",
                    "debian",
                    "suse",
                    "fedora",
                    "mint",
                    "kali",
                    "arch",
                ]
            ):
                return "Linux"

            # Unix family
            elif any(
                unix in os_lower for unix in ["unix", "aix", "solaris", "hpux", "hp-ux"]
            ):
                return "Unix"

            # macOS family
            elif any(mac in os_lower for mac in ["mac", "darwin", "osx", "macos"]):
                return "macOS"

            # BSD family
            elif any(
                bsd in os_lower for bsd in ["bsd", "freebsd", "openbsd", "netbsd"]
            ):
                return "BSD"

            # Other
            else:
                return "Other"

        except Exception:
            return "Unknown"

    def extract_numeric_value(self, value) -> Optional[int]:
        """Extract numeric value from various formats."""
        try:
            if value is None:
                return None

            # If it's already numeric
            if isinstance(value, (int, float)):
                # Check for NaN
                if value != value:  # NaN check
                    return None
                return int(value)

            # If it's a string, try to extract numbers
            if isinstance(value, str):
                value_clean = value.strip()
                if not value_clean or value_clean.lower() in [
                    "",
                    "unknown",
                    "n/a",
                    "null",
                    "none",
                ]:
                    return None

                # Try direct conversion first
                try:
                    return int(float(value_clean))
                except ValueError:
                    pass

                # Extract numbers with regex
                numbers = re.findall(r"\d+", value_clean.replace(",", ""))
                if numbers:
                    return int(numbers[0])

            return None

        except (ValueError, TypeError):
            return None

    def expand_abbreviation(self, field: str, abbrev: str) -> str:
        """Expand common abbreviations based on field context."""
        try:
            abbrev_lower = abbrev.lower().strip()

            if field == "asset_type":
                expansions = {
                    "srv": "Server",
                    "db": "Database",
                    "ws": "Workstation",
                    "fw": "Firewall",
                    "lb": "Load Balancer",
                    "sw": "Switch",
                    "rtr": "Router",
                    "vm": "Virtual Machine",
                    "app": "Application",
                    "web": "Web Server",
                }
                return expansions.get(abbrev_lower, abbrev.title())

            elif field == "environment":
                expansions = {
                    "dev": "Development",
                    "prod": "Production",
                    "test": "Testing",
                    "stage": "Staging",
                    "uat": "UAT",
                    "qa": "QA",
                    "dr": "Disaster Recovery",
                    "sb": "Sandbox",
                }
                return expansions.get(abbrev_lower, abbrev.title())

            elif field == "department":
                expansions = {
                    "it": "IT Operations",
                    "hr": "Human Resources",
                    "fin": "Finance",
                    "ops": "Operations",
                    "dev": "Development",
                    "qa": "Quality Assurance",
                    "sec": "Security",
                    "net": "Network",
                    "db": "Database",
                    "app": "Application",
                }
                return expansions.get(abbrev_lower, abbrev.title())

            else:
                # Generic expansions
                generic_expansions = {
                    "mgmt": "Management",
                    "admin": "Administration",
                    "svc": "Service",
                    "sys": "System",
                    "net": "Network",
                    "sec": "Security",
                    "biz": "Business",
                }
                return generic_expansions.get(abbrev_lower, abbrev.title())

        except Exception:
            return abbrev.title() if abbrev else ""

    def group_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Group items by a specific field and count occurrences."""
        try:
            groups = {}
            for item in items:
                value = item.get(field, "Unknown")
                # Handle None values
                if value is None:
                    value = "Unknown"
                groups[str(value)] = groups.get(str(value), 0) + 1
            return groups
        except Exception as e:
            logger.warning(f"Error grouping by field {field}: {e}")
            return {}

    def calculate_percentage(self, part: int, total: int) -> float:
        """Calculate percentage with safe division."""
        try:
            if total == 0:
                return 0.0
            return round((part / total) * 100, 2)
        except Exception:
            return 0.0

    def clean_for_display(self, value: Any) -> str:
        """Clean value for display purposes."""
        try:
            if value is None:
                return "Unknown"

            if isinstance(value, (list, dict)):
                return str(value)

            value_str = str(value).strip()
            if not value_str or value_str.lower() in ["none", "null", "nan", ""]:
                return "Unknown"

            return value_str
        except Exception:
            return "Unknown"

    def format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            if not timestamp:
                return "Unknown"

            # Handle ISO format timestamps
            if "T" in timestamp:
                return timestamp.split("T")[0]  # Return just the date part

            return timestamp
        except Exception:
            return "Unknown"

    def validate_required_fields(
        self, asset: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate that required fields are present and not empty."""
        try:
            missing_fields = []

            for field in required_fields:
                value = asset.get(field)
                if value is None or str(value).strip() in [
                    "",
                    "Unknown",
                    "null",
                    "None",
                    "N/A",
                ]:
                    missing_fields.append(field)

            return missing_fields
        except Exception as e:
            logger.warning(f"Error validating required fields: {e}")
            return required_fields  # Assume all are missing on error

    def generate_asset_summary(self, assets: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for a list of assets."""
        try:
            if not assets:
                return {
                    "total": 0,
                    "by_type": {},
                    "by_environment": {},
                    "by_department": {},
                    "by_criticality": {},
                    "by_os_family": {},
                    "health_score": 0,
                }

            summary = {
                "total": len(assets),
                "by_type": self.group_by_field(assets, "type"),
                "by_environment": self.group_by_field(assets, "environment"),
                "by_department": self.group_by_field(assets, "department"),
                "by_criticality": self.group_by_field(assets, "criticality"),
                "by_os_family": self.group_by_field(assets, "os_family"),
                "health_score": self._calculate_health_score(assets),
            }

            return summary

        except Exception as e:
            logger.warning(f"Error generating asset summary: {e}")
            return {"total": len(assets) if assets else 0, "error": str(e)}

    def _calculate_health_score(self, assets: List[Dict]) -> int:
        """Calculate overall health score for assets."""
        try:
            if not assets:
                return 0

            total_score = 0
            for asset in assets:
                # Score based on data completeness
                score = 100

                # Deduct for missing critical fields
                critical_fields = [
                    "hostname",
                    "ip_address",
                    "asset_type",
                    "environment",
                ]
                missing_fields = self.validate_required_fields(asset, critical_fields)
                score -= len(missing_fields) * 15

                # Deduct for unknown values
                if asset.get("department") in [None, "Unknown", ""]:
                    score -= 10
                if asset.get("criticality") in [None, "Unknown", ""]:
                    score -= 10

                total_score += max(0, score)

            return int(total_score / len(assets))

        except Exception:
            return 75  # Default reasonable score
