"""
Asset Processing Utilities
Contains asset type determination, field mapping, and data transformation utilities.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AssetProcessingUtils:
    """Utility class for asset processing operations"""

    @staticmethod
    def determine_asset_type(
        asset: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> str:
        """Determine asset type from asset data using field mappings"""

        # PRIORITY 0: Check if asset_type is already set by the crew
        crew_type = AssetProcessingUtils._check_crew_asset_type(asset)
        if crew_type:
            return crew_type

        # Extract field values using mappings
        asset_data = AssetProcessingUtils._extract_asset_fields(asset, field_mappings)

        # Run classification pipeline
        asset_type = (
            AssetProcessingUtils._classify_by_direct_mapping(asset_data)
            or AssetProcessingUtils._classify_by_os(asset_data)
            or AssetProcessingUtils._classify_by_name(asset_data)
            or AssetProcessingUtils._classify_by_advanced_patterns(asset_data)
            or AssetProcessingUtils._classify_by_combined_text(asset_data)
        )

        if asset_type:
            return asset_type

        # Default classification
        logger.warning(
            f"Unable to determine asset type for asset: {asset_data['asset_name']}, defaulting to 'server'"
        )
        return "server"

    @staticmethod
    def _check_crew_asset_type(asset: Dict[str, Any]) -> Optional[str]:
        """Check if asset_type is already set by the crew"""
        if "asset_type" in asset and asset["asset_type"]:
            crew_asset_type = str(asset["asset_type"]).lower()
            if crew_asset_type in ["server", "application", "database", "device"]:
                return crew_asset_type
        return None

    @staticmethod
    def _extract_asset_fields(
        asset: Dict[str, Any], field_mappings: Dict[str, str]
    ) -> Dict[str, str]:
        """Extract and map asset fields for classification"""
        # Get field mappings
        asset_type_field = None
        asset_name_field = None
        os_field = None

        for source_field, target_field in field_mappings.items():
            if target_field == "asset_type":
                asset_type_field = source_field
            elif target_field == "asset_name":
                asset_name_field = source_field
            elif target_field == "operating_system":
                os_field = source_field

        # Extract values using mapped fields AND direct asset keys
        asset_type = (
            asset.get(asset_type_field, "")
            if asset_type_field
            else asset.get("asset_type", "")
        )
        asset_name = (
            asset.get(asset_name_field, "")
            if asset_name_field
            else asset.get("asset_name", asset.get("name", ""))
        )
        os_info = (
            asset.get(os_field, "")
            if os_field
            else asset.get("operating_system", asset.get("os", ""))
        )

        return {
            "asset_type": str(asset_type).lower(),
            "asset_name": str(asset_name).lower(),
            "os_info": str(os_info).lower(),
        }

    @staticmethod
    def _classify_by_direct_mapping(asset_data: Dict[str, str]) -> Optional[str]:
        """Classify by direct asset type mapping from field mappings"""
        asset_type_lower = asset_data["asset_type"]
        if not asset_type_lower:
            return None

        server_keywords = ["server", "host", "vm", "virtual"]
        app_keywords = ["application", "app", "service", "software"]
        device_keywords = ["network", "device", "router", "switch", "firewall"]

        if any(keyword in asset_type_lower for keyword in server_keywords):
            return "server"
        elif any(keyword in asset_type_lower for keyword in app_keywords):
            return "application"
        elif "database" in asset_type_lower or "db" in asset_type_lower:
            return "database"
        elif any(keyword in asset_type_lower for keyword in device_keywords):
            return "device"

        return None

    @staticmethod
    def _classify_by_os(asset_data: Dict[str, str]) -> Optional[str]:
        """Classify by OS information (typically indicates servers)"""
        os_info_lower = asset_data["os_info"]
        if not os_info_lower:
            return None

        os_keywords = [
            "linux",
            "windows",
            "unix",
            "centos",
            "ubuntu",
            "redhat",
            "solaris",
            "aix",
        ]

        if any(os in os_info_lower for os in os_keywords):
            return "server"

        return None

    @staticmethod
    def _classify_by_name(asset_data: Dict[str, str]) -> Optional[str]:
        """Classify by asset name patterns"""
        asset_name_lower = asset_data["asset_name"]
        if not asset_name_lower:
            return None

        server_keywords = ["server", "host", "vm", "srv"]
        app_keywords = ["app", "api", "service", "web"]
        db_keywords = ["db", "database", "mysql", "postgresql", "oracle", "sql"]
        device_keywords = ["device", "network", "router", "switch", "firewall"]

        if any(keyword in asset_name_lower for keyword in server_keywords):
            return "server"
        elif any(keyword in asset_name_lower for keyword in app_keywords):
            return "application"
        elif any(keyword in asset_name_lower for keyword in db_keywords):
            return "database"
        elif any(keyword in asset_name_lower for keyword in device_keywords):
            return "device"

        return None

    @staticmethod
    def _classify_by_advanced_patterns(asset_data: Dict[str, str]) -> Optional[str]:
        """Advanced pattern matching for specific asset types"""
        asset_type_lower = asset_data["asset_type"]
        asset_name_lower = asset_data["asset_name"]

        # Advanced application patterns
        app_type_keywords = ["web", "api", "microservice"]
        app_name_keywords = ["payment", "user", "order", "inventory"]

        if any(keyword in asset_type_lower for keyword in app_type_keywords) or any(
            keyword in asset_name_lower for keyword in app_name_keywords
        ):
            return "application"

        # Advanced database patterns
        db_type_keywords = ["mysql", "postgresql", "oracle", "sql", "mongo", "redis"]
        db_name_keywords = ["userdb", "orderdb", "paymentdb"]

        if any(keyword in asset_type_lower for keyword in db_type_keywords) or any(
            keyword in asset_name_lower for keyword in db_name_keywords
        ):
            return "database"

        return None

    @staticmethod
    def _classify_by_combined_text(asset_data: Dict[str, str]) -> Optional[str]:
        """Classify based on combined text analysis"""
        all_asset_text = f"{asset_data['asset_name']} {asset_data['asset_type']} {asset_data['os_info']}"

        server_keywords = [
            "server",
            "host",
            "vm",
            "linux",
            "windows",
            "ubuntu",
            "centos",
        ]
        app_keywords = ["app", "web", "api", "service", "ui", "frontend", "backend"]
        db_keywords = ["db", "database", "mysql", "postgres", "oracle", "mongo"]
        device_keywords = ["network", "router", "switch", "firewall", "device"]

        if any(keyword in all_asset_text for keyword in server_keywords):
            return "server"
        elif any(keyword in all_asset_text for keyword in app_keywords):
            return "application"
        elif any(keyword in all_asset_text for keyword in db_keywords):
            return "database"
        elif any(keyword in all_asset_text for keyword in device_keywords):
            return "device"

        return None

    @staticmethod
    def get_mapped_value(
        asset: Dict[str, Any], target_field: str, field_mappings: Dict[str, str]
    ) -> Any:
        """Get value from asset using field mappings"""
        # First, try to get the value directly from the target field (if data was already processed)
        if target_field in asset:
            return asset.get(target_field)

        # Find the source field that maps to the target field
        source_field = None
        for source, target in field_mappings.items():
            if target == target_field:
                source_field = source
                break

        # Return the value from the source field if found
        if source_field:
            # Try original data first
            if "_original" in asset and source_field in asset["_original"]:
                return asset["_original"][source_field]
            # Then try the asset itself
            return asset.get(source_field)

        return None

    @staticmethod
    def parse_int(value: Any) -> Optional[int]:
        """Safely parse integer value"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_float(value: Any) -> Optional[float]:
        """Safely parse float value"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def generate_unique_asset_name(
        original_name: str, idx: int, seen_names: set
    ) -> str:
        """Generate a unique asset name, handling duplicates and empty names"""
        # Handle empty names (database constraint requires non-empty name)
        if not original_name:
            asset_name = f"Asset-{idx + 1}"  # Simple numeric identifier
        else:
            asset_name = original_name

        # Ensure unique names by adding suffix if needed
        counter = 1
        base_name = asset_name
        while asset_name in seen_names:
            if base_name:
                asset_name = f"{base_name}-{counter}"
            else:
                asset_name = f"Asset-{idx + 1}-{counter}"
            counter += 1

        return asset_name
