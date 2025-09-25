"""
Collection Bulk Import Asset Management
Handles asset creation and updates for bulk import operations.

DEPRECATED: This module is being replaced by app.config.asset_mappings.

The functions in this module are now wrappers around the data-driven
configuration system for backward compatibility.
"""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.application import Application
from app.models.server import Server
from app.models.database import Database
from app.models.device import Device

# Import the new configuration-driven implementation
from app.config.asset_mappings import (
    create_or_update_asset as config_create_or_update_asset,
)


def _safe_int_cast(value: Any, default: int = 0) -> int:
    """Safely cast a value to integer, returning default if conversion fails.

    Args:
        value: The value to convert to integer
        default: Default value to return if conversion fails

    Returns:
        Integer value or default if conversion fails

    Raises:
        None - always returns a valid integer
    """
    if value is None or value == "":
        return default

    try:
        # Handle string values that might have whitespace
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default

        return int(float(value))  # Use float first to handle decimal strings
    except (ValueError, TypeError, OverflowError):
        return default


async def create_or_update_asset(
    asset_type: str, data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Any:
    """Create or update an asset based on type and data.

    DEPRECATED: This function now delegates to the configuration-driven
    implementation in app.config.asset_mappings for maintainability.
    """
    # Delegate to the new configuration-driven implementation
    return await config_create_or_update_asset(asset_type, data, db, context)


async def _handle_application(
    data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Optional[Application]:
    """Create or update an application asset."""
    app_name = data.get("application_name", "")
    if not app_name:
        return None

    result = await db.execute(
        select(Application).where(
            Application.name == app_name,
            Application.engagement_id == context.engagement_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        asset = Application(
            id=uuid.uuid4(),
            name=app_name,
            business_criticality=data.get("business_criticality", "Medium"),
            description=data.get("description", ""),
            technology_stack=(
                {"technologies": data.get("technology_stack", [])}
                if isinstance(data.get("technology_stack"), list)
                else data.get("technology_stack", {})
            ),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(asset)
    else:
        # Update existing
        asset.business_criticality = data.get(
            "business_criticality", asset.business_criticality
        )
        asset.description = data.get("description", asset.description)
        asset.updated_at = datetime.now(timezone.utc)

    return asset


async def _handle_server(
    data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Optional[Server]:
    """Create or update a server asset."""
    server_name = data.get("server_name", "")
    if not server_name:
        return None

    result = await db.execute(
        select(Server).where(
            Server.name == server_name,
            Server.engagement_id == context.engagement_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        asset = Server(
            id=uuid.uuid4(),
            name=server_name,
            hostname=data.get("hostname", ""),
            ip_address=data.get("ip_address", ""),
            operating_system=data.get("operating_system", ""),
            cpu_cores=_safe_int_cast(data.get("cpu_cores"), 0),
            memory_gb=_safe_int_cast(data.get("memory_gb"), 0),
            storage_gb=_safe_int_cast(data.get("storage_gb"), 0),
            environment=data.get("environment", "Production"),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(asset)
    else:
        # Update existing
        asset.hostname = data.get("hostname", asset.hostname)
        asset.ip_address = data.get("ip_address", asset.ip_address)
        asset.updated_at = datetime.now(timezone.utc)

    return asset


async def _handle_database(
    data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Optional[Database]:
    """Create or update a database asset."""
    db_name = data.get("database_name", "")
    if not db_name:
        return None

    result = await db.execute(
        select(Database).where(
            Database.name == db_name,
            Database.engagement_id == context.engagement_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        asset = Database(
            id=uuid.uuid4(),
            name=db_name,
            database_type=data.get("database_type", ""),
            version=data.get("version", ""),
            size_gb=_safe_int_cast(data.get("size_gb"), 0),
            criticality=data.get("criticality", "Medium"),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(asset)
    else:
        # Update existing
        asset.database_type = data.get("database_type", asset.database_type)
        asset.version = data.get("version", asset.version)
        asset.updated_at = datetime.now(timezone.utc)

    return asset


async def _handle_device(
    data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Optional[Device]:
    """Create or update a device asset."""
    device_name = data.get("device_name", "")
    if not device_name:
        return None

    result = await db.execute(
        select(Device).where(
            Device.name == device_name,
            Device.engagement_id == context.engagement_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        asset = Device(
            id=uuid.uuid4(),
            name=device_name,
            device_type=data.get("device_type", ""),
            manufacturer=data.get("manufacturer", ""),
            model=data.get("model", ""),
            serial_number=data.get("serial_number", ""),
            location=data.get("location", ""),
            criticality=data.get("criticality", "Medium"),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(asset)
    else:
        # Update existing
        asset.manufacturer = data.get("manufacturer", asset.manufacturer)
        asset.model = data.get("model", asset.model)
        asset.updated_at = datetime.now(timezone.utc)

    return asset
