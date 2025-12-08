"""
Data extractors for IntelligentGapScanner - Extract values from 6 sources.

Extracts data extraction methods (JSONB, enrichment, canonical apps, related assets)
from main scanner to keep main scanner class under 400 lines.

CC Generated for Issue #1111 - IntelligentGapScanner Modularization
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture

Updated for Issue #1193: Check related asset data (servers) using field aliases
from CriticalAttributesDefinition to inherit OS, virtualization, tech stack.
"""

import logging
from typing import Any, Dict, List, Optional

from app.models import Asset, CanonicalApplication
from app.services.collection.critical_attributes import CriticalAttributesDefinition

logger = logging.getLogger(__name__)


class DataExtractors:
    """Data extraction methods for IntelligentGapScanner (6 sources)."""

    def extract_from_jsonb(
        self,
        custom_attributes: Optional[Dict[str, Any]],
        enrichment_data: Optional[Dict[str, Any]],
        field_id: str,
    ) -> Optional[Any]:
        """
        Extract value from custom_attributes or enrichment_data JSONB fields.

        Args:
            custom_attributes: assets.custom_attributes JSONB
            enrichment_data: assets.enrichment_data JSONB
            field_id: Field to extract (e.g., "database_type")

        Returns:
            Value if found, None otherwise
        """
        # Check custom_attributes first
        if custom_attributes and isinstance(custom_attributes, dict):
            if field_id in custom_attributes:
                return custom_attributes[field_id]
            # Try variations (db_type, database-type, etc.)
            for key in custom_attributes.keys():
                if self._field_matches(key, field_id):
                    return custom_attributes[key]

        # Check enrichment_data second
        if enrichment_data and isinstance(enrichment_data, dict):
            if field_id in enrichment_data:
                return enrichment_data[field_id]
            # Try variations
            for key in enrichment_data.keys():
                if self._field_matches(key, field_id):
                    return enrichment_data[key]

        return None

    def extract_from_enrichment(
        self, enrichment: Dict[str, Optional[Any]], field_id: str
    ) -> Optional[Any]:
        """
        Extract value from enrichment tables (tech_debt, performance, cost).

        Args:
            enrichment: Dict from DataLoaders.load_enrichment_data()
            field_id: Field to extract (e.g., "resilience_tier")

        Returns:
            Value if found in enrichment tables, None otherwise
        """
        if not enrichment:
            return None

        # Direct match
        if field_id in enrichment:
            return enrichment[field_id]

        # Fuzzy match for common variations
        enrichment_field_map = {
            "resilience": "resilience_tier",
            "code_quality": "code_quality_score",
            "response_time": "avg_response_time_ms",
            "cpu": "peak_cpu_percent",
            "cost": "estimated_monthly_cost",
            "rightsizing": "rightsizing_recommendation",
        }

        for pattern, canonical_field in enrichment_field_map.items():
            if pattern in field_id.lower() and canonical_field in enrichment:
                return enrichment[canonical_field]

        return None

    def extract_from_canonical_apps(
        self, canonical_apps: List[CanonicalApplication], field_id: str
    ) -> Optional[Any]:
        """
        Extract value from canonical_applications junction.

        Args:
            canonical_apps: List from DataLoaders.load_canonical_applications()
            field_id: Field to extract (e.g., "canonical_application_name")

        Returns:
            Value if found, None otherwise
        """
        if not canonical_apps:
            return None

        # Fields that can be derived from canonical apps
        if field_id in [
            "canonical_application_name",
            "canonical_app_name",
            "application_name",
        ]:
            return canonical_apps[0].name if canonical_apps else None

        if field_id in ["canonical_application_id", "canonical_app_id"]:
            return str(canonical_apps[0].id) if canonical_apps else None

        # Database type from database canonical applications
        if field_id == "database_type" and canonical_apps:
            # If this is a database application, return its canonical_name
            # (e.g., "PostgreSQL", "MySQL", "Oracle")
            for app in canonical_apps:
                if (
                    hasattr(app, "application_type")
                    and app.application_type == "database"
                ):
                    return app.canonical_name
                # Also check if canonical_name suggests it's a database
                if hasattr(app, "canonical_name"):
                    db_keywords = [
                        "postgres",
                        "mysql",
                        "oracle",
                        "mongodb",
                        "redis",
                        "sql",
                    ]
                    name_lower = app.canonical_name.lower()
                    if any(keyword in name_lower for keyword in db_keywords):
                        return app.canonical_name

        if "application" in field_id.lower() and canonical_apps:
            # Generic application-related field - return first app name
            return canonical_apps[0].name

        return None

    def extract_from_related_assets(
        self, related_assets: List[Asset], field_id: str
    ) -> Optional[Any]:
        """
        Extract value from related assets (via asset_dependencies).

        Uses CriticalAttributesDefinition for field alias resolution to find values
        even when stored under alternate keys (e.g., 'os' for 'operating_system').

        Fix for Issue #1193: Now checks technical_details JSONB and uses field
        aliases so application questionnaires consider data from underlying servers.

        Args:
            related_assets: List from DataLoaders.load_related_assets()
            field_id: Field to extract (e.g., "operating_system", "technology_stack")

        Returns:
            Value if found in related assets, None otherwise
        """
        if not related_assets:
            return None

        # Check if field_id has "related_" prefix
        if field_id.startswith("related_"):
            actual_field = field_id.replace("related_", "")
        else:
            actual_field = field_id

        # Get field aliases from CriticalAttributesDefinition
        field_aliases = self._get_field_aliases(actual_field)

        # Try to find field in related assets using all aliases
        for related_asset in related_assets:
            for alias in field_aliases:
                value = self._extract_value_from_alias(related_asset, alias)
                if value:
                    return value

        return None

    def _get_field_aliases(self, field_id: str) -> List[str]:
        """
        Get all field aliases for a given field_id from CriticalAttributesDefinition.

        This ensures we check all possible locations where the data might be stored.

        Args:
            field_id: The field to look up (e.g., "operating_system")

        Returns:
            List of aliases to check (e.g., ["operating_system", "os_version", "custom_attributes.os"])
        """
        aliases = [field_id]  # Always include the original field

        # Get attribute mappings from CriticalAttributesDefinition
        attr_mappings = CriticalAttributesDefinition.get_attribute_mapping()

        # Check if field_id matches any attribute name or is in asset_fields
        for attr_name, attr_config in attr_mappings.items():
            asset_fields = attr_config.get("asset_fields", [])

            # If field_id matches the attribute name, add all its asset_fields
            if attr_name == field_id or field_id in asset_fields:
                for field in asset_fields:
                    if field not in aliases:
                        aliases.append(field)

            # Also check partial matches for common field name patterns
            # E.g., "operating_system" should match "operating_system_version"
            if field_id in attr_name or attr_name.startswith(field_id):
                for field in asset_fields:
                    if field not in aliases:
                        aliases.append(field)

        return aliases

    def _extract_value_from_alias(self, asset: Asset, alias: str) -> Optional[Any]:
        """
        Extract value from a specific alias path on an asset.

        Handles three patterns:
        - Direct column: "operating_system" -> asset.operating_system
        - custom_attributes path: "custom_attributes.os" -> asset.custom_attributes["os"]
        - technical_details path: Check technical_details JSONB as fallback

        Args:
            asset: Asset to extract from
            alias: Alias path (e.g., "operating_system", "custom_attributes.os")

        Returns:
            Value if found, None otherwise
        """
        # Handle custom_attributes.* path
        if alias.startswith("custom_attributes."):
            key = alias.replace("custom_attributes.", "")
            if asset.custom_attributes and key in asset.custom_attributes:
                value = asset.custom_attributes[key]
                if value is not None and value != "" and value != []:
                    return value
            # Also check technical_details for this key
            if asset.technical_details and key in asset.technical_details:
                value = asset.technical_details[key]
                if value is not None and value != "" and value != []:
                    return value
            return None

        # Handle other dot-notation paths (e.g., resilience.rto_minutes)
        if "." in alias:
            parts = alias.split(".")
            # Skip enrichment table paths - those are handled by enrichment loader
            if parts[0] in ["resilience", "compliance_flags", "vulnerabilities"]:
                return None
            return None

        # Handle direct column access
        if hasattr(asset, alias):
            value = getattr(asset, alias, None)
            if value is not None and value != "" and value != []:
                return value

        # Fallback: Check custom_attributes with the alias as key
        if asset.custom_attributes and alias in asset.custom_attributes:
            value = asset.custom_attributes[alias]
            if value is not None and value != "" and value != []:
                return value

        # Fallback: Check technical_details with the alias as key
        if asset.technical_details and alias in asset.technical_details:
            value = asset.technical_details[alias]
            if value is not None and value != "" and value != []:
                return value

        return None

    def _field_matches(self, key: str, field_id: str) -> bool:
        """Check if JSONB key matches field_id with common variations."""
        key_lower = key.lower().replace("_", "").replace("-", "")
        field_lower = field_id.lower().replace("_", "").replace("-", "")
        return key_lower == field_lower
