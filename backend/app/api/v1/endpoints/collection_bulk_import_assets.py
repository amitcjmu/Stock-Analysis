"""
Collection Bulk Import Asset Management

DEPRECATED: This module is being replaced by app.config.asset_mappings.

This module now contains only a wrapper function for backward compatibility.
All asset-specific handlers have been removed in favor of the data-driven
configuration system in app.config.asset_mappings.
"""

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

# Import the new configuration-driven implementation
from app.config.asset_mappings import (
    create_or_update_asset as config_create_or_update_asset,
)


async def create_or_update_asset(
    asset_type: str, data: Dict[str, Any], db: AsyncSession, context: RequestContext
) -> Any:
    """Create or update an asset based on type and data.

    DEPRECATED: This function now delegates to the configuration-driven
    implementation in app.config.asset_mappings for maintainability.

    All asset-specific handlers have been removed. The new implementation uses
    a data-driven approach via app.config.asset_mappings which handles all asset
    types (application, server, database, device) through configuration rather
    than individual handler functions.
    """
    # Delegate to the new configuration-driven implementation
    return await config_create_or_update_asset(asset_type, data, db, context)
