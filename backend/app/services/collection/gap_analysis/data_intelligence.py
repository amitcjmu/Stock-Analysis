"""
Data Intelligence Module for Gap Analysis

This module provides intelligent checking of existing asset data to avoid
creating gaps for fields that already have data in JSONB columns.

Per COLLECTION_FLOW_TWO_CRITICAL_ISSUES.md, gap analysis should check:
- custom_attributes JSONB field
- technical_details JSONB field
- Standard model fields

Before creating a gap, we verify the data doesn't already exist.
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.asset import Asset
from app.services.crewai_flows.tools.critical_attributes_tool.base import (
    CriticalAttributesDefinition,
)

logger = logging.getLogger(__name__)


class DataIntelligence:
    """Intelligent data checking for gap analysis."""

    # Attribute to field mapping from CriticalAttributesDefinition
    ATTRIBUTE_MAPPING = CriticalAttributesDefinition.ATTRIBUTE_FIELD_MAPPING

    @classmethod
    def get_existing_fields(cls, asset: Asset) -> Dict[str, Any]:
        """
        Extract all existing data from asset including JSONB fields.

        Args:
            asset: Asset model instance

        Returns:
            Dictionary mapping attribute names to their values

        Example:
            >>> asset = Asset(name="WebApp", custom_attributes={"cpu_cores": 4})
            >>> DataIntelligence.get_existing_fields(asset)
            {'cpu_memory_storage_specs': '4 cores', ...}
        """
        existing_fields = {}

        # Iterate through all 22 critical attributes
        for attr_name, attr_config in cls.ATTRIBUTE_MAPPING.items():
            asset_fields = attr_config.get("asset_fields", [])

            # Check each potential field location for this attribute
            for field in asset_fields:
                value = cls._get_field_value(asset, field)
                if value is not None and value != "":
                    existing_fields[attr_name] = value
                    break  # Found value, no need to check other fields

        return existing_fields

    @classmethod
    def _get_field_value(cls, asset: Asset, field_path: str) -> Optional[Any]:
        """
        Get value from asset field, supporting dot notation for JSONB.

        Args:
            asset: Asset model instance
            field_path: Field path (e.g., "name" or "custom_attributes.cpu_cores")

        Returns:
            Field value if it exists and is not empty, None otherwise

        Example:
            >>> _get_field_value(asset, "custom_attributes.cpu_cores")
            4
            >>> _get_field_value(asset, "nonexistent_field")
            None
        """
        if "." in field_path:
            # JSONB field access (e.g., "custom_attributes.cpu_cores")
            parts = field_path.split(".", 1)
            jsonb_field_name = parts[0]
            jsonb_key = parts[1]

            # Get JSONB field from asset
            jsonb_data = getattr(asset, jsonb_field_name, None)

            if jsonb_data and isinstance(jsonb_data, dict):
                value = jsonb_data.get(jsonb_key)
                return value if cls._is_meaningful_value(value) else None

        else:
            # Standard model field access
            if hasattr(asset, field_path):
                value = getattr(asset, field_path)
                return value if cls._is_meaningful_value(value) else None

        return None

    @classmethod
    def _is_meaningful_value(cls, value: Any) -> bool:
        """
        Check if value is meaningful (not None, empty string, or placeholder).

        Args:
            value: Value to check

        Returns:
            True if value contains meaningful data, False otherwise

        Example:
            >>> _is_meaningful_value(None)
            False
            >>> _is_meaningful_value("")
            False
            >>> _is_meaningful_value("Unknown")
            False
            >>> _is_meaningful_value("Windows Server 2019")
            True
        """
        if value is None:
            return False

        if isinstance(value, str):
            value_lower = value.strip().lower()
            # Reject empty strings and common placeholders
            if not value_lower:
                return False
            if value_lower in [
                "unknown",
                "n/a",
                "na",
                "null",
                "none",
                "tbd",
                "pending",
                "not set",
            ]:
                return False

        # For lists, check if non-empty
        if isinstance(value, list):
            return len(value) > 0

        # For dicts, check if non-empty
        if isinstance(value, dict):
            return len(value) > 0

        # For numbers, 0 is meaningful
        if isinstance(value, (int, float)):
            return True

        # For booleans, both True and False are meaningful
        if isinstance(value, bool):
            return True

        # Any other non-None, non-empty value is meaningful
        return True

    @classmethod
    def check_attribute_exists(cls, asset: Asset, attribute_name: str) -> bool:
        """
        Check if data exists for a specific critical attribute.

        Args:
            asset: Asset model instance
            attribute_name: Name of critical attribute to check

        Returns:
            True if data exists, False if gap should be created

        Example:
            >>> asset = Asset(custom_attributes={"cpu_cores": 4})
            >>> DataIntelligence.check_attribute_exists(asset, "cpu_memory_storage_specs")
            True  # Data exists, no gap needed
        """
        attr_config = cls.ATTRIBUTE_MAPPING.get(attribute_name)
        if not attr_config:
            logger.warning(f"Unknown attribute: {attribute_name}")
            return False

        asset_fields = attr_config.get("asset_fields", [])

        # Check if any field for this attribute has data
        for field in asset_fields:
            value = cls._get_field_value(asset, field)
            if value is not None:
                logger.debug(f"Attribute {attribute_name} exists in {field}: {value}")
                return True

        return False

    @classmethod
    def get_missing_attributes(
        cls, asset: Asset, applicable_attributes: List[str]
    ) -> List[str]:
        """
        Get list of attributes that are missing for this asset.

        Args:
            asset: Asset model instance
            applicable_attributes: List of attributes applicable to this asset type

        Returns:
            List of attribute names that are missing (gaps to create)

        Example:
            >>> asset = Asset(asset_type="application", name="WebApp")
            >>> applicable = ["operating_system_version", "cpu_memory_storage_specs"]
            >>> DataIntelligence.get_missing_attributes(asset, applicable)
            ["operating_system_version", "cpu_memory_storage_specs"]  # Both missing
        """
        missing = []

        for attr_name in applicable_attributes:
            if not cls.check_attribute_exists(asset, attr_name):
                missing.append(attr_name)

        logger.debug(
            f"Asset {asset.name} ({asset.asset_type}): "
            f"{len(missing)} missing out of {len(applicable_attributes)} applicable attributes"
        )

        return missing

    @classmethod
    def analyze_asset_completeness(cls, asset: Asset) -> Dict[str, Any]:
        """
        Comprehensive analysis of asset data completeness.

        Args:
            asset: Asset model instance

        Returns:
            Dictionary with completeness statistics

        Example:
            >>> asset = Asset(...)
            >>> DataIntelligence.analyze_asset_completeness(asset)
            {
                'total_attributes': 22,
                'existing_count': 8,
                'missing_count': 14,
                'completeness_percentage': 36.4,
                'existing_fields': {...},
                'missing_fields': [...]
            }
        """
        existing_fields = cls.get_existing_fields(asset)
        existing_count = len(existing_fields)
        total_count = len(cls.ATTRIBUTE_MAPPING)
        missing_count = total_count - existing_count

        completeness_percentage = (
            (existing_count / total_count * 100) if total_count > 0 else 0
        )

        all_attribute_names = list(cls.ATTRIBUTE_MAPPING.keys())
        missing_fields = [
            attr for attr in all_attribute_names if attr not in existing_fields
        ]

        return {
            "total_attributes": total_count,
            "existing_count": existing_count,
            "missing_count": missing_count,
            "completeness_percentage": round(completeness_percentage, 1),
            "existing_fields": existing_fields,
            "missing_fields": missing_fields,
        }
