"""
Asset Type Overlay Configuration Loader
Provides tenant-aware configuration for asset type requirements.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default overlay configuration
DEFAULT_OVERLAYS = {
    "base": {
        "required_fields": [
            {
                "field": "name",
                "category": "basic",
                "gap_message": "Asset name is required",
                "6r_impact": ["all"],
            },
            {
                "field": "business_criticality",
                "category": "business",
                "gap_message": "Business criticality assessment needed",
                "6r_impact": ["retire", "retain"],
            },
            {
                "field": "technology_stack",
                "category": "technical",
                "gap_message": "Technical stack documentation required",
                "6r_impact": ["replatform", "refactor"],
            },
        ],
        "optional_fields": [
            {"field": "data_classification", "category": "compliance"},
            {"field": "maintenance_windows", "category": "operational"},
        ],
    },
    "database": {
        "required_fields": [
            {
                "field": "database_type",
                "category": "technical",
                "gap_message": "Database type must be specified",
                "6r_impact": ["replatform"],
            },
            {
                "field": "data_volume",
                "category": "technical",
                "gap_message": "Data volume assessment needed for migration planning",
                "6r_impact": ["rehost", "replatform"],
            },
            {
                "field": "backup_strategy",
                "category": "operational",
                "gap_message": "Backup strategy documentation required",
                "6r_impact": ["all"],
            },
        ]
    },
    "application": {
        "required_fields": [
            {
                "field": "architecture_pattern",
                "category": "technical",
                "gap_message": "Architecture pattern needed for migration strategy",
                "6r_impact": ["refactor", "replatform"],
            },
            {
                "field": "user_count",
                "category": "business",
                "gap_message": "User count required for capacity planning",
                "6r_impact": ["all"],
            },
            {
                "field": "integration_points",
                "category": "technical",
                "gap_message": "Integration points must be documented",
                "6r_impact": ["refactor", "repurchase"],
            },
        ]
    },
    "service": {
        "required_fields": [
            {
                "field": "api_interfaces",
                "category": "technical",
                "gap_message": "API interfaces must be documented",
                "6r_impact": ["refactor", "repurchase"],
            },
            {
                "field": "sla_requirements",
                "category": "business",
                "gap_message": "SLA requirements needed",
                "6r_impact": ["all"],
            },
            {
                "field": "scalability_requirements",
                "category": "technical",
                "gap_message": "Scalability requirements must be defined",
                "6r_impact": ["replatform", "refactor"],
            },
        ]
    },
    "infrastructure": {
        "required_fields": [
            {
                "field": "compute_requirements",
                "category": "technical",
                "gap_message": "Compute requirements must be specified",
                "6r_impact": ["rehost", "replatform"],
            },
            {
                "field": "network_topology",
                "category": "technical",
                "gap_message": "Network topology documentation required",
                "6r_impact": ["replatform", "refactor"],
            },
            {
                "field": "security_zones",
                "category": "security",
                "gap_message": "Security zone mapping required",
                "6r_impact": ["all"],
            },
        ]
    },
}


class OverlayLoader:
    """Loads and manages asset type overlay configurations."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the overlay loader.

        Args:
            config_path: Optional path to custom overlay configuration file
        """
        self.config_path = config_path
        self.overlays = self._load_overlays()

    def _load_overlays(self) -> Dict[str, Any]:
        """Load overlay configurations from file or use defaults."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    custom_overlays = json.load(f)
                    logger.info(f"Loaded custom overlays from {self.config_path}")
                    # Merge with defaults, custom takes precedence
                    merged = DEFAULT_OVERLAYS.copy()
                    merged.update(custom_overlays)
                    return merged
            except Exception as e:
                logger.warning(
                    f"Failed to load custom overlays from {self.config_path}: {e}"
                )
                return DEFAULT_OVERLAYS
        else:
            return DEFAULT_OVERLAYS

    def get_overlay(
        self, asset_type: str, tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get overlay configuration for an asset type.

        Args:
            asset_type: Type of asset (e.g., 'database', 'application')
            tenant_id: Optional tenant ID for tenant-specific overlays

        Returns:
            Overlay configuration dictionary
        """
        # In future, could load tenant-specific overlays from database
        # For now, use the configured overlays

        base_overlay = self.overlays.get("base", {})
        type_overlay = self.overlays.get(asset_type.lower(), {})

        # Merge overlays: base + type-specific
        result = {
            "required_fields": base_overlay.get("required_fields", []).copy(),
            "optional_fields": base_overlay.get("optional_fields", []).copy(),
        }

        # Add type-specific required fields
        if "required_fields" in type_overlay:
            result["required_fields"].extend(type_overlay["required_fields"])

        # Add type-specific optional fields
        if "optional_fields" in type_overlay:
            result["optional_fields"].extend(type_overlay["optional_fields"])

        return result


# Global singleton instance
_overlay_loader = None


def get_overlay_loader(config_path: Optional[Path] = None) -> OverlayLoader:
    """
    Get the global overlay loader instance.

    Args:
        config_path: Optional path to custom configuration file

    Returns:
        OverlayLoader instance
    """
    global _overlay_loader
    if _overlay_loader is None:
        _overlay_loader = OverlayLoader(config_path)
    return _overlay_loader
