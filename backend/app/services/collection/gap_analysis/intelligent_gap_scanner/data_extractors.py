"""
Data extractors for IntelligentGapScanner - Extract values from 6 sources.

Extracts data extraction methods (JSONB, enrichment, canonical apps, related assets)
from main scanner to keep main scanner class under 400 lines.

CC Generated for Issue #1111 - IntelligentGapScanner Modularization
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import logging
from typing import Any, Dict, List, Optional

from app.models import Asset, CanonicalApplication

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

        if "application" in field_id.lower() and canonical_apps:
            # Generic application-related field - return first app name
            return canonical_apps[0].name

        return None

    def extract_from_related_assets(
        self, related_assets: List[Asset], field_id: str
    ) -> Optional[Any]:
        """
        Extract value from related assets (via asset_dependencies).

        Args:
            related_assets: List from DataLoaders.load_related_assets()
            field_id: Field to extract (e.g., "related_database_type")

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

        # Try to find field in related assets
        for related_asset in related_assets:
            # Check standard column
            if hasattr(related_asset, actual_field):
                value = getattr(related_asset, actual_field, None)
                if value:
                    return value

            # Check custom_attributes
            if (
                related_asset.custom_attributes
                and actual_field in related_asset.custom_attributes
            ):
                return related_asset.custom_attributes[actual_field]

        return None

    def _field_matches(self, key: str, field_id: str) -> bool:
        """Check if JSONB key matches field_id with common variations."""
        key_lower = key.lower().replace("_", "").replace("-", "")
        field_lower = field_id.lower().replace("_", "").replace("-", "")
        return key_lower == field_lower
