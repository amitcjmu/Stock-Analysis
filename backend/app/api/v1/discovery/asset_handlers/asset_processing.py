"""
Asset Processing Handler
Handles asset data processing, transformation, and reprocessing operations.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class AssetProcessingHandler:
    """Handles asset data processing and transformation operations."""

    def __init__(self):
        self.persistence_available = False
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Initialize optional dependencies with graceful fallbacks."""
        try:
            from app.api.v1.discovery.persistence import (
                backup_processed_assets,
                get_processed_assets,
            )

            self.get_processed_assets = get_processed_assets
            self.backup_processed_assets = backup_processed_assets
            self.persistence_available = True
            logger.info("Asset processing services initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Asset processing services not available: {e}")
            self.persistence_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    async def reprocess_stored_assets(self) -> Dict[str, Any]:
        """
        Reprocess stored assets with updated algorithms.
        """
        try:
            if not self.persistence_available:
                return self._fallback_reprocess()

            all_assets = self.get_processed_assets()

            if not all_assets:
                return {
                    "status": "success",
                    "message": "No assets to reprocess",
                    "processed_count": 0,
                }

            reprocessed_count = 0

            for asset in all_assets:
                try:
                    # Add reprocessing timestamp
                    asset["reprocessed_timestamp"] = pd.Timestamp.now().isoformat()

                    # Apply enhanced processing logic
                    self._enhance_asset_data(asset)

                    reprocessed_count += 1

                except Exception as e:
                    logger.warning(
                        f"Error reprocessing asset {asset.get('id', 'unknown')}: {e}"
                    )
                    continue

            # Save the updated assets
            if reprocessed_count > 0:
                self.backup_processed_assets()

            return {
                "status": "success",
                "message": f"Successfully reprocessed {reprocessed_count} assets",
                "processed_count": reprocessed_count,
                "total_assets": len(all_assets),
            }

        except Exception as e:
            logger.error(f"Error reprocessing assets: {e}")
            return self._fallback_reprocess()

    async def get_applications_for_analysis(
        self,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get applications data specially formatted for 6R analysis.
        """
        try:
            if not self.persistence_available:
                return self._fallback_get_applications()

            # Get assets with client/engagement scoping if available
            if client_account_id and hasattr(self, "get_processed_assets_scoped"):
                all_assets = self.get_processed_assets_scoped(
                    client_account_id, engagement_id
                )
            else:
                all_assets = self.get_processed_assets()

            if not all_assets:
                return {
                    "applications": [],
                    "summary": {
                        "total_applications": 0,
                        "by_complexity": {},
                        "by_environment": {},
                        "by_department": {},
                        "technology_distribution": {},
                    },
                }

            # Filter and transform assets into applications
            applications = []
            for asset in all_assets:
                # Only include application-type assets
                asset_type = str(asset.get("asset_type", "")).lower()
                if (
                    "app" in asset_type
                    or "service" in asset_type
                    or "application" in asset_type
                ):
                    app_data = self._transform_asset_for_analysis(asset)
                    applications.append(app_data)

            # Generate summary statistics
            summary = self._generate_applications_summary(applications)

            return {"applications": applications, "summary": summary}

        except Exception as e:
            logger.error(f"Error getting applications for analysis: {e}")
            return self._fallback_get_applications()

    async def get_unlinked_assets(
        self,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get assets that are NOT tied to any application - critical for migration planning.
        """
        try:
            if not self.persistence_available:
                return self._fallback_get_unlinked_assets()

            # Get all assets with client/engagement scoping if available
            if client_account_id and hasattr(self, "get_processed_assets_scoped"):
                all_assets = self.get_processed_assets_scoped(
                    client_account_id, engagement_id
                )
            else:
                all_assets = self.get_processed_assets()

            if not all_assets:
                return {
                    "unlinked_assets": [],
                    "summary": {
                        "total_unlinked": 0,
                        "by_type": {},
                        "by_environment": {},
                        "by_criticality": {},
                        "migration_impact": "low",
                    },
                }

            # Filter out application-type assets - these are the ones that get applications
            unlinked_assets = []
            application_names = set()

            # First pass: collect all application names
            for asset in all_assets:
                asset_type = str(asset.get("asset_type", "")).lower()
                if (
                    "app" in asset_type
                    or "service" in asset_type
                    or "application" in asset_type
                ):
                    app_name = asset.get("asset_name", "").lower()
                    if app_name:
                        application_names.add(app_name)

            # Second pass: find assets not linked to applications
            for asset in all_assets:
                asset_type = str(asset.get("asset_type", "")).lower()

                # Skip application assets themselves
                if (
                    "app" in asset_type
                    or "service" in asset_type
                    or "application" in asset_type
                ):
                    continue

                # Check if this asset is linked to any application
                asset_name = asset.get("asset_name", "").lower()
                is_linked = False

                # Check various ways assets might be linked to applications
                for app_name in application_names:
                    if app_name in asset_name or asset_name in app_name:
                        is_linked = True
                        break

                    # Check hostname/IP relationships
                    hostname = asset.get("hostname", "").lower()
                    ip_address = asset.get("ip_address", "")
                    if (hostname and app_name in hostname) or (
                        ip_address and app_name in ip_address
                    ):
                        is_linked = True
                        break

                # If not linked, add to unlinked assets
                if not is_linked:
                    unlinked_asset = self._transform_asset_for_unlinked_analysis(asset)
                    unlinked_assets.append(unlinked_asset)

            # Generate summary statistics
            summary = self._generate_unlinked_summary(unlinked_assets)

            return {"unlinked_assets": unlinked_assets, "summary": summary}

        except Exception as e:
            logger.error(f"Error getting unlinked assets: {e}")
            return self._fallback_get_unlinked_assets()

    def _transform_asset_for_unlinked_analysis(
        self, asset: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform raw asset data for unlinked asset analysis.
        """
        transformed = {
            "id": asset.get("id")
            or asset.get("ci_id")
            or asset.get("asset_id", "unknown"),
            "name": asset.get("asset_name") or asset.get("hostname", "Unknown Asset"),
            "type": asset.get("asset_type", "Unknown"),
            "environment": asset.get("environment", "Unknown"),
            "department": asset.get("department")
            or asset.get("business_owner", "Unknown"),
            "criticality": self._map_criticality(
                asset.get("status") or asset.get("criticality", "Medium")
            ),
            "hostname": asset.get("hostname", ""),
            "ip_address": asset.get("ip_address", ""),
            "operating_system": asset.get("operating_system", ""),
            "cpu_cores": self._extract_numeric_value(asset.get("cpu_cores")),
            "memory_gb": self._extract_numeric_value(asset.get("memory_gb")),
            "storage_gb": self._extract_numeric_value(asset.get("storage_gb")),
            "location": asset.get("location", ""),
            "last_updated": asset.get("updated_timestamp")
            or asset.get("reprocessed_timestamp", ""),
            "migration_consideration": self._assess_unlinked_migration_consideration(
                asset
            ),
        }

        return transformed

    def _assess_unlinked_migration_consideration(self, asset: Dict[str, Any]) -> str:
        """
        Assess what to consider for unlinked assets during migration.
        """
        asset_type = str(asset.get("asset_type", "")).lower()

        if "server" in asset_type:
            return "May require application mapping or could be infrastructure-only"
        elif "database" in asset_type:
            return "Critical - requires application dependency analysis"
        elif "network" in asset_type:
            return "Infrastructure dependency - assess network requirements"
        elif "storage" in asset_type:
            return "Storage dependency - assess data migration needs"
        elif "security" in asset_type:
            return "Security infrastructure - assess compliance requirements"
        else:
            return "Requires classification and dependency analysis"

    def _generate_unlinked_summary(self, unlinked_assets: List[Dict]) -> Dict[str, Any]:
        """
        Generate summary statistics for unlinked assets.
        """
        if not unlinked_assets:
            return {
                "total_unlinked": 0,
                "by_type": {},
                "by_environment": {},
                "by_criticality": {},
                "migration_impact": "none",
            }

        # Calculate migration impact based on asset types and criticality
        critical_count = len(
            [a for a in unlinked_assets if a.get("criticality", "").lower() == "high"]
        )
        database_count = len(
            [a for a in unlinked_assets if "database" in a.get("type", "").lower()]
        )

        if critical_count > 5 or database_count > 3:
            migration_impact = "high"
        elif critical_count > 2 or database_count > 1:
            migration_impact = "medium"
        else:
            migration_impact = "low"

        summary = {
            "total_unlinked": len(unlinked_assets),
            "by_type": self._group_by_field(unlinked_assets, "type"),
            "by_environment": self._group_by_field(unlinked_assets, "environment"),
            "by_criticality": self._group_by_field(unlinked_assets, "criticality"),
            "migration_impact": migration_impact,
        }

        return summary

    def _enhance_asset_data(self, asset: Dict[str, Any]) -> None:
        """
        Apply enhanced processing to asset data.
        """
        try:
            # Standardize asset types
            if "asset_type" in asset:
                asset["asset_type"] = self._standardize_asset_type(asset["asset_type"])

            # Normalize environment values
            if "environment" in asset:
                asset["environment"] = self._standardize_environment(
                    asset["environment"]
                )

            # Extract and standardize technology stack
            tech_stack = self._build_tech_stack_from_asset(asset)
            if tech_stack:
                asset["technology_stack"] = tech_stack

            # Calculate complexity score
            asset["complexity_score"] = self._calculate_complexity_score(asset)

            # Assess business value
            asset["business_value_score"] = self._get_business_value_score(asset)

            # Assess data sensitivity
            asset["data_sensitivity"] = self._assess_data_sensitivity(asset)

            # Assess compliance requirements
            asset["compliance_requirements"] = self._assess_compliance_requirements(
                asset
            )

            # Assess technical debt
            asset["technical_debt_level"] = self._assess_technical_debt(asset)

            # Assess modernization potential
            asset["modernization_potential"] = self._assess_modernization_potential(
                asset
            )

            # Assess cloud readiness
            asset["cloud_readiness"] = self._assess_cloud_readiness(asset)

            # Generate application tags
            asset["tags"] = self._generate_application_tags(asset)

        except Exception as e:
            logger.warning(f"Error enhancing asset data: {e}")

    def _transform_asset_for_analysis(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw asset data for 6R analysis.
        """
        transformed = {
            "id": asset.get("id")
            or asset.get("ci_id")
            or asset.get("asset_id", "unknown"),
            "name": asset.get("asset_name")
            or asset.get("hostname", "Unknown Application"),
            "type": "Application",
            "environment": asset.get("environment", "Unknown"),
            "department": asset.get("department")
            or asset.get("business_owner", "Unknown"),
            "criticality": self._map_criticality(
                asset.get("status") or asset.get("criticality", "Medium")
            ),
            "technology_stack": asset.get("technology_stack")
            or self._build_tech_stack_from_asset(asset),
            "complexity_score": asset.get("complexity_score")
            or self._calculate_complexity_score(asset),
            "business_value_score": asset.get("business_value_score")
            or self._get_business_value_score(asset),
            "data_sensitivity": asset.get("data_sensitivity")
            or self._assess_data_sensitivity(asset),
            "compliance_requirements": asset.get("compliance_requirements")
            or self._assess_compliance_requirements(asset),
            "technical_debt_level": asset.get("technical_debt_level")
            or self._assess_technical_debt(asset),
            "modernization_potential": asset.get("modernization_potential")
            or self._assess_modernization_potential(asset),
            "cloud_readiness": asset.get("cloud_readiness")
            or self._assess_cloud_readiness(asset),
            "dependencies": asset.get("dependencies", []),
            "tags": asset.get("tags") or self._generate_application_tags(asset),
            "cpu_cores": self._extract_numeric_value(asset.get("cpu_cores")),
            "memory_gb": self._extract_numeric_value(asset.get("memory_gb")),
            "storage_gb": self._extract_numeric_value(asset.get("storage_gb")),
            "os_family": self._standardize_os_family(asset.get("operating_system", "")),
            "ip_address": asset.get("ip_address", ""),
            "hostname": asset.get("hostname", ""),
            "last_updated": asset.get("updated_timestamp")
            or asset.get("reprocessed_timestamp", ""),
        }

        return transformed

    def _generate_applications_summary(
        self, applications: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for applications.
        """
        if not applications:
            return {
                "total_applications": 0,
                "by_complexity": {},
                "by_environment": {},
                "by_department": {},
                "technology_distribution": {},
            }

        summary = {
            "total_applications": len(applications),
            "by_complexity": self._get_complexity_distribution(applications),
            "by_environment": self._group_by_field(applications, "environment"),
            "by_department": self._group_by_field(applications, "department"),
            "technology_distribution": self._extract_technology_distribution(
                applications
            ),
        }

        return summary

    # Utility methods from original file
    def _standardize_asset_type(self, asset_type: str) -> str:
        """Standardize asset type values."""
        if not asset_type:
            return "Unknown"

        asset_type_lower = asset_type.lower().strip()

        # Application types
        if any(
            term in asset_type_lower
            for term in ["app", "application", "service", "web"]
        ):
            return "Application"

        # Server types
        if any(
            term in asset_type_lower for term in ["server", "host", "vm", "virtual"]
        ):
            return "Server"

        # Database types
        if any(
            term in asset_type_lower
            for term in ["database", "db", "sql", "mongo", "oracle"]
        ):
            return "Database"

        # Network types
        if any(
            term in asset_type_lower
            for term in ["network", "switch", "router", "firewall"]
        ):
            return "Network Device"

        # Storage types
        if any(term in asset_type_lower for term in ["storage", "nas", "san", "disk"]):
            return "Storage"

        return asset_type.title()

    def _standardize_environment(self, environment: str) -> str:
        """Standardize environment values."""
        if not environment:
            return "Unknown"

        env_lower = environment.lower().strip()

        if env_lower in ["prod", "production", "live"]:
            return "Production"
        elif env_lower in ["stage", "staging", "uat", "preprod"]:
            return "Staging"
        elif env_lower in ["dev", "development", "develop"]:
            return "Development"
        elif env_lower in ["test", "testing", "qa"]:
            return "Test"

        return environment.title()

    def _standardize_os_family(self, os_name: str) -> str:
        """Standardize operating system family."""
        if not os_name:
            return "Unknown"

        os_lower = os_name.lower()

        if any(term in os_lower for term in ["windows", "win"]):
            return "Windows"
        elif any(
            term in os_lower
            for term in ["linux", "ubuntu", "redhat", "centos", "debian"]
        ):
            return "Linux"
        elif any(term in os_lower for term in ["unix", "aix", "solaris"]):
            return "Unix"
        elif any(term in os_lower for term in ["mac", "darwin"]):
            return "macOS"

        return "Other"

    def _calculate_complexity_score(self, asset: Dict[str, Any]) -> int:
        """Calculate complexity score based on asset characteristics."""
        score = 1  # Base score

        # Technology stack complexity
        tech_stack = asset.get("technology_stack", "")
        if tech_stack:
            tech_count = len(tech_stack.split(","))
            score += min(tech_count, 5)  # Cap at 5 points

        # Resource complexity
        cpu_cores = self._extract_numeric_value(asset.get("cpu_cores", 0))
        if cpu_cores and cpu_cores > 4:
            score += 2

        memory_gb = self._extract_numeric_value(asset.get("memory_gb", 0))
        if memory_gb and memory_gb > 16:
            score += 2

        # Environment factor
        env = asset.get("environment", "").lower()
        if env == "production":
            score += 3
        elif env in ["staging", "uat"]:
            score += 2

        return min(score, 10)  # Cap at 10

    def _get_business_value_score(self, asset: Dict[str, Any]) -> int:
        """Calculate business value score."""
        score = 5  # Default medium value

        criticality = asset.get("criticality", "").lower()
        if criticality in ["high", "critical"]:
            score = 9
        elif criticality == "medium":
            score = 6
        elif criticality == "low":
            score = 3

        return score

    def _assess_data_sensitivity(self, asset: Dict[str, Any]) -> str:
        """Assess data sensitivity level."""
        asset_name = str(asset.get("asset_name", "")).lower()
        tech_stack = str(asset.get("technology_stack", "")).lower()

        # High sensitivity indicators
        if any(
            term in asset_name + tech_stack
            for term in ["payment", "finance", "bank", "pii", "customer"]
        ):
            return "High"

        # Medium sensitivity indicators
        if any(
            term in asset_name + tech_stack
            for term in ["user", "account", "profile", "auth"]
        ):
            return "Medium"

        return "Low"

    def _assess_compliance_requirements(self, asset: Dict[str, Any]) -> List[str]:
        """Assess compliance requirements."""
        requirements = []

        asset_name = str(asset.get("asset_name", "")).lower()
        tech_stack = str(asset.get("technology_stack", "")).lower()
        data_sensitivity = self._assess_data_sensitivity(asset)

        if data_sensitivity == "High":
            requirements.extend(["PCI-DSS", "SOX"])

        if any(
            term in asset_name + tech_stack for term in ["health", "medical", "patient"]
        ):
            requirements.append("HIPAA")

        if any(term in asset_name + tech_stack for term in ["eu", "europe", "gdpr"]):
            requirements.append("GDPR")

        environment = asset.get("environment", "").lower()
        if environment == "production":
            requirements.append("SOC-2")

        return list(set(requirements))  # Remove duplicates

    def _assess_technical_debt(self, asset: Dict[str, Any]) -> str:
        """Assess technical debt level."""
        os_name = str(asset.get("operating_system", "")).lower()

        # High debt indicators
        if any(term in os_name for term in ["2008", "2012", "xp", "vista", "legacy"]):
            return "High"

        # Medium debt indicators
        if any(term in os_name for term in ["2016", "2019", "old"]):
            return "Medium"

        return "Low"

    def _assess_modernization_potential(self, asset: Dict[str, Any]) -> str:
        """Assess modernization potential."""
        complexity = self._calculate_complexity_score(asset)
        tech_debt = self._assess_technical_debt(asset)

        if complexity <= 3 and tech_debt == "Low":
            return "High"
        elif complexity <= 6 and tech_debt != "High":
            return "Medium"
        else:
            return "Low"

    def _assess_cloud_readiness(self, asset: Dict[str, Any]) -> str:
        """Assess cloud readiness level."""
        tech_stack = str(asset.get("technology_stack", "")).lower()
        modernization = self._assess_modernization_potential(asset)

        # High readiness indicators
        if any(
            term in tech_stack
            for term in ["docker", "kubernetes", "microservice", "api"]
        ):
            return "High"

        # Use modernization potential as proxy
        return modernization

    def _generate_application_tags(self, asset: Dict[str, Any]) -> List[str]:
        """Generate tags for the application."""
        tags = []

        # Technology tags
        tech_stack = str(asset.get("technology_stack", "")).lower()
        if "java" in tech_stack:
            tags.append("java")
        if "python" in tech_stack:
            tags.append("python")
        if "nodejs" in tech_stack or "node.js" in tech_stack:
            tags.append("nodejs")
        if any(db in tech_stack for db in ["mysql", "postgres", "oracle", "mongodb"]):
            tags.append("database")
        if any(term in tech_stack for term in ["web", "http", "rest", "api"]):
            tags.append("web-service")

        # Environment tags
        env = asset.get("environment", "").lower()
        if env == "production":
            tags.append("production")

        # Criticality tags
        criticality = asset.get("criticality", "").lower()
        if criticality in ["high", "critical"]:
            tags.append("mission-critical")

        # Complexity tags
        complexity = self._calculate_complexity_score(asset)
        if complexity >= 7:
            tags.append("complex")

        return tags

    def _build_tech_stack_from_asset(self, asset: Dict[str, Any]) -> str:
        """Build technology stack string from asset data."""
        tech_components = []

        # Operating system
        os_name = asset.get("operating_system", "")
        if os_name:
            tech_components.append(os_name)

        # Try to extract from asset name or description
        asset_name = str(asset.get("asset_name", "")).lower()

        # Common technology patterns
        if "java" in asset_name:
            tech_components.append("Java")
        if "python" in asset_name:
            tech_components.append("Python")
        if "node" in asset_name:
            tech_components.append("Node.js")
        if any(db in asset_name for db in ["mysql", "postgres", "oracle", "mongo"]):
            tech_components.append("Database")
        if "web" in asset_name:
            tech_components.append("Web Server")

        return ", ".join(tech_components) if tech_components else "Unknown"

    def _map_criticality(self, status: str) -> str:
        """Map various status values to standard criticality levels."""
        if not status:
            return "Medium"

        status_lower = status.lower().strip()

        if status_lower in ["critical", "high", "production", "tier1", "1"]:
            return "High"
        elif status_lower in ["medium", "moderate", "tier2", "2"]:
            return "Medium"
        elif status_lower in ["low", "tier3", "3"]:
            return "Low"

        return "Medium"

    def _extract_numeric_value(self, value) -> Optional[int]:
        """Extract numeric value from various formats."""
        if value is None:
            return None

        try:
            # If it's already numeric
            if isinstance(value, (int, float)):
                return int(value) if not pd.isna(value) else None

            # If it's a string, try to extract numbers
            if isinstance(value, str):
                import re

                match = re.search(r"(\d+)", value.replace(",", ""))
                if match:
                    return int(match.group(1))

            return None
        except (ValueError, TypeError):
            return None

    def _group_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Group items by a specific field and count occurrences."""
        groups = {}
        for item in items:
            value = item.get(field, "Unknown")
            groups[value] = groups.get(value, 0) + 1
        return groups

    def _extract_technology_distribution(
        self, applications: List[Dict]
    ) -> Dict[str, int]:
        """Extract technology distribution from applications."""
        tech_counts = {}

        for app in applications:
            tech_stack = app.get("technology_stack", "")
            if tech_stack:
                technologies = [tech.strip() for tech in tech_stack.split(",")]
                for tech in technologies:
                    if tech and tech != "Unknown":
                        tech_counts[tech] = tech_counts.get(tech, 0) + 1

        return tech_counts

    def _get_complexity_distribution(self, applications: List[Dict]) -> Dict[str, int]:
        """Get complexity distribution."""
        distribution = {"Low": 0, "Medium": 0, "High": 0}

        for app in applications:
            score = app.get("complexity_score", 5)
            if score <= 3:
                distribution["Low"] += 1
            elif score <= 7:
                distribution["Medium"] += 1
            else:
                distribution["High"] += 1

        return distribution

    # Fallback methods
    def _fallback_reprocess(self) -> Dict[str, Any]:
        """Fallback reprocess method."""
        return {
            "status": "error",
            "message": "Asset processing service not available",
            "processed_count": 0,
            "fallback_mode": True,
        }

    def _fallback_get_applications(self) -> Dict[str, Any]:
        """Fallback get applications method."""
        return {
            "applications": [],
            "summary": {
                "total_applications": 0,
                "by_complexity": {},
                "by_environment": {},
                "by_department": {},
                "technology_distribution": {},
            },
            "fallback_mode": True,
        }

    def _fallback_get_unlinked_assets(self) -> Dict[str, Any]:
        """Fallback get unlinked assets method."""
        return {
            "unlinked_assets": [],
            "summary": {
                "total_unlinked": 0,
                "by_type": {},
                "by_environment": {},
                "by_criticality": {},
                "migration_impact": "none",
            },
            "fallback_mode": True,
        }
