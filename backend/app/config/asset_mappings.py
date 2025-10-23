"""
Asset Mappings Configuration
Data-driven configuration for bulk import operations supporting different asset types.

This module provides:
1. Asset type configurations with model classes, unique keys, and CSV field mappings
2. Generic logic for create_or_update_asset operations
3. Generic logic for map_csv_to_questionnaire operations

This replaces hardcoded if/elif chains with maintainable, scalable configuration.
"""

from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.canonical_applications import CanonicalApplication
from app.models.server import Server
from app.models.database import Database
from app.models.device import Device


@dataclass
class FieldMapping:
    """Configuration for mapping CSV fields to questionnaire fields."""

    csv_field: str
    questionnaire_field: str
    default_value: Any = ""
    transform_func: Optional[Callable[[Any], Any]] = None
    required: bool = False


@dataclass
class AssetTypeConfig:
    """Configuration for an asset type in the bulk import system."""

    model_class: Type
    unique_field: str  # Field used for duplicate detection
    csv_mappings: List[FieldMapping] = field(default_factory=list)

    def get_unique_field_value(self, data: Dict[str, Any]) -> str:
        """Extract the unique field value from questionnaire data."""
        return data.get(self.unique_field, "")


def _split_comma_separated(value: Any) -> List[str]:
    """Transform function to split comma-separated strings into lists."""
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value if isinstance(value, list) else []


def _safe_int_cast(value: Any, default: int = 0) -> int:
    """Safely cast a value to integer, returning default if conversion fails."""
    if value is None or value == "":
        return default

    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        return int(float(value))
    except (ValueError, TypeError, OverflowError):
        return default


# Asset type configurations
ASSET_TYPE_CONFIGS: Dict[str, AssetTypeConfig] = {
    "applications": AssetTypeConfig(
        model_class=CanonicalApplication,
        unique_field="application_name",
        csv_mappings=[
            FieldMapping("Application Name", "application_name", required=True),
            FieldMapping("Business Criticality", "business_criticality", "Medium"),
            FieldMapping("Application Owner", "application_owner", ""),
            FieldMapping("Technical Owner", "technical_owner", ""),
            FieldMapping("Description", "description", ""),
            FieldMapping(
                "Technology Stack", "technology_stack", [], _split_comma_separated
            ),
            FieldMapping("Deployment Type", "deployment_type", "On-Premise"),
            FieldMapping("Migration Priority", "migration_priority", "Medium"),
            FieldMapping("Dependencies", "dependencies", ""),
            FieldMapping("Compliance Requirements", "compliance_requirements", ""),
        ],
    ),
    "servers": AssetTypeConfig(
        model_class=Server,
        unique_field="server_name",
        csv_mappings=[
            FieldMapping("Server Name", "server_name", required=True),
            FieldMapping("Hostname", "hostname", ""),
            FieldMapping("IP Address", "ip_address", ""),
            FieldMapping("Operating System", "operating_system", ""),
            FieldMapping("OS Version", "os_version", ""),
            FieldMapping("CPU Cores", "cpu_cores", 0, _safe_int_cast),
            FieldMapping("Memory (GB)", "memory_gb", 0, _safe_int_cast),
            FieldMapping("Storage (GB)", "storage_gb", 0, _safe_int_cast),
            FieldMapping("Environment", "environment", "Production"),
            FieldMapping("Virtualization", "virtualization", "Physical"),
        ],
    ),
    "databases": AssetTypeConfig(
        model_class=Database,
        unique_field="database_name",
        csv_mappings=[
            FieldMapping("Database Name", "database_name", required=True),
            FieldMapping("Database Type", "database_type", ""),
            FieldMapping("Version", "version", ""),
            FieldMapping("Size (GB)", "size_gb", 0, _safe_int_cast),
            FieldMapping("Criticality", "criticality", "Medium"),
            FieldMapping("Backup Frequency", "backup_frequency", ""),
            FieldMapping("RTO", "recovery_time_objective", ""),
            FieldMapping("RPO", "recovery_point_objective", ""),
            FieldMapping("Compliance Requirements", "compliance_requirements", ""),
            FieldMapping("Hosted On Server", "hosted_on_server", ""),
        ],
    ),
    "devices": AssetTypeConfig(
        model_class=Device,
        unique_field="device_name",
        csv_mappings=[
            FieldMapping("Device Name", "device_name", required=True),
            FieldMapping("Device Type", "device_type", ""),
            FieldMapping("Manufacturer", "manufacturer", ""),
            FieldMapping("Model", "model", ""),
            FieldMapping("Serial Number", "serial_number", ""),
            FieldMapping("Location", "location", ""),
            FieldMapping("Network Connectivity", "network_connectivity", ""),
            FieldMapping("Management Interface", "management_interface", ""),
            FieldMapping("Criticality", "criticality", "Medium"),
            FieldMapping("Migration Approach", "migration_approach", ""),
        ],
    ),
}


def get_asset_config(asset_type: str) -> AssetTypeConfig:
    """Get configuration for the specified asset type."""
    if asset_type not in ASSET_TYPE_CONFIGS:
        raise ValueError(f"Unsupported asset type: {asset_type}")
    return ASSET_TYPE_CONFIGS[asset_type]


def map_csv_to_questionnaire(
    csv_row: Dict[str, Any], asset_type: str
) -> Dict[str, Any]:
    """Generic CSV to questionnaire mapping using configuration."""
    config = get_asset_config(asset_type)

    questionnaire_data = {
        "metadata": {
            "source": "bulk_import",
            "imported_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    # Apply field mappings
    for mapping in config.csv_mappings:
        csv_value = csv_row.get(mapping.csv_field, mapping.default_value)

        # Apply transformation if specified
        if mapping.transform_func:
            csv_value = mapping.transform_func(csv_value)
        elif csv_value is None or csv_value == "":
            csv_value = mapping.default_value

        questionnaire_data[mapping.questionnaire_field] = csv_value

    return questionnaire_data


async def create_or_update_asset(
    asset_type: str, data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Any:
    """Generic asset creation/update using configuration."""
    config = get_asset_config(asset_type)
    model_class = config.model_class

    # Extract unique identifier
    unique_value = config.get_unique_field_value(data)
    if not unique_value:
        return None

    # Map questionnaire field name to model field name
    model_field_name = _get_model_field_name(config.unique_field)

    # Find existing asset
    result = await db.execute(
        select(model_class).where(
            getattr(model_class, model_field_name) == unique_value,
            model_class.engagement_id == context.engagement_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        # Create new asset
        asset_data = _prepare_asset_data(data, config, context, is_create=True)
        asset = model_class(**asset_data)
        db.add(asset)
    else:
        # Update existing asset
        asset_data = _prepare_asset_data(data, config, context, is_create=False)
        for field_name, value in asset_data.items():
            if hasattr(asset, field_name) and field_name not in [
                "id",
                "created_at",
                "client_account_id",
                "engagement_id",
            ]:
                setattr(asset, field_name, value)

    return asset


def _get_model_field_name(questionnaire_field: str) -> str:
    """Map questionnaire field names to model field names."""
    # Most fields map directly, but handle special cases
    field_mapping = {
        "application_name": "name",
        "server_name": "name",
        "database_name": "name",
        "device_name": "name",
    }
    return field_mapping.get(questionnaire_field, questionnaire_field)


def _prepare_asset_data(
    data: Dict[str, Any],
    config: AssetTypeConfig,
    context: RequestContext,
    is_create: bool = False,
) -> Dict[str, Any]:
    """Prepare asset data for creation or update."""
    import uuid
    from datetime import datetime, timezone

    asset_data = {}

    if is_create:
        # Fields only set during creation
        asset_data.update(
            {
                "id": uuid.uuid4(),
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "created_at": datetime.now(timezone.utc),
            }
        )

    # Always update timestamp for both create and update
    asset_data["updated_at"] = datetime.now(timezone.utc)

    # Map data fields based on asset type
    if config.model_class == CanonicalApplication:
        asset_data.update(
            {
                "name": data.get("application_name", ""),
                "business_criticality": data.get("business_criticality", "Medium"),
                "description": data.get("description", ""),
                "technology_stack": (
                    {"technologies": data.get("technology_stack", [])}
                    if isinstance(data.get("technology_stack"), list)
                    else data.get("technology_stack", {})
                ),
            }
        )
    elif config.model_class == Server:
        asset_data.update(
            {
                "name": data.get("server_name", ""),
                "hostname": data.get("hostname", ""),
                "ip_address": data.get("ip_address", ""),
                "operating_system": data.get("operating_system", ""),
                "cpu_cores": data.get("cpu_cores", 0),
                "memory_gb": data.get("memory_gb", 0),
                "storage_gb": data.get("storage_gb", 0),
                "environment": data.get("environment", "Production"),
            }
        )
    elif config.model_class == Database:
        asset_data.update(
            {
                "name": data.get("database_name", ""),
                "database_type": data.get("database_type", ""),
                "version": data.get("version", ""),
                "size_gb": data.get("size_gb", 0),
                "criticality": data.get("criticality", "Medium"),
            }
        )
    elif config.model_class == Device:
        asset_data.update(
            {
                "name": data.get("device_name", ""),
                "device_type": data.get("device_type", ""),
                "manufacturer": data.get("manufacturer", ""),
                "model": data.get("model", ""),
                "serial_number": data.get("serial_number", ""),
                "location": data.get("location", ""),
                "criticality": data.get("criticality", "Medium"),
            }
        )

    return asset_data
