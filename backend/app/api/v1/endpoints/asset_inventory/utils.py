"""
Utility functions for Asset Inventory operations.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def get_asset_data(
    asset_ids: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    context: Optional[RequestContext] = None,
    db: Optional[Session] = None,
):
    """Get asset data based on IDs or filters with proper multitenancy filtering."""
    try:
        # IMPORTANT: Enforce multitenancy - if context is available, filter by it
        if context and context.client_account_id and context.engagement_id:
            # Use database query with context filtering
            from app.core.database import get_db
            from app.models.asset import Asset
            from sqlalchemy import select

            # If no db session provided, get one
            if db is None:
                # This is a simplified approach for sync session
                # In practice, we should use dependency injection
                logger.warning("No database session provided to get_asset_data")
                return []

            # Use the repository pattern for proper context filtering
            from app.repositories.asset_repository import AssetRepository

            repo = AssetRepository(db, context.client_account_id)

            if asset_ids:
                # Get multiple assets by IDs
                assets = []
                for asset_id in asset_ids:
                    asset = await repo.get_by_id(asset_id)
                    if asset:
                        assets.append(asset)
            else:
                # Get all assets for the context
                assets = await repo.get_all(limit=1000)  # Reasonable limit

            # Convert to dict format
            return [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "criticality": asset.criticality,
                    "status": asset.status,
                    "six_r_strategy": asset.six_r_strategy,
                    "migration_wave": asset.migration_wave,
                    "application_name": asset.application_name,
                    "hostname": asset.hostname,
                    "operating_system": asset.operating_system,
                    "cpu_cores": asset.cpu_cores,
                    "memory_gb": asset.memory_gb,
                    "storage_gb": asset.storage_gb,
                }
                for asset in assets
            ]
        else:
            # Fallback to persistence layer with warning
            logger.warning(
                "No context available for multitenancy filtering - returning empty dataset for security"
            )
            return []

    except ImportError:
        logger.warning("Asset persistence not available, using empty dataset")
        return []
    except Exception as e:
        logger.error(f"Failed to get asset data: {e}")
        return []
