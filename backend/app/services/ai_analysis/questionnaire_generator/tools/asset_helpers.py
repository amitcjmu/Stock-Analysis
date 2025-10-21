"""
Asset Helper Utilities
Helper functions for asset name and type lookup.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AssetHelpers:
    """Helper class for asset name and type lookups."""

    def __init__(self):
        """Initialize asset helpers with caching."""
        self._asset_name_cache: Dict[str, str] = {}

    async def get_asset_name(
        self, asset_id: str, business_context: Dict[str, Any] = None
    ) -> str:
        """
        Fetch asset name from business_context, database, or cache.

        CRITICAL FIX: Uses actual asset names instead of UUID prefix.
        Resolves issue where questions showed "Asset df0d34a9" instead of "Admin Dashboard".

        Priority order:
        1. business_context['asset_names'] dict (passed from caller)
        2. Cache from previous lookups
        3. Database query (if db_session available)
        4. Fallback to "Asset {uuid_prefix}" (preserves existing behavior)

        Args:
            asset_id: Asset UUID as string
            business_context: Optional dict with asset_names mapping

        Returns:
            Asset name or "Asset {uuid_prefix}" as fallback
        """
        # Check business_context first (most efficient)
        if business_context and "asset_names" in business_context:
            asset_names = business_context["asset_names"]
            if asset_id in asset_names:
                asset_name = asset_names[asset_id]
                self._asset_name_cache[asset_id] = asset_name
                return asset_name

        # Check cache
        if asset_id in self._asset_name_cache:
            return self._asset_name_cache[asset_id]

        # Fallback to UUID prefix (preserves existing behavior for cases where asset_names not provided)
        fallback_name = f"Asset {asset_id[:8]}"
        logger.debug(f"⚠️ Using UUID prefix for {asset_id}: {fallback_name}")
        self._asset_name_cache[asset_id] = fallback_name
        return fallback_name

    async def get_asset_type(
        self, asset_id: str, business_context: Dict[str, Any] = None
    ) -> str:
        """
        Retrieve asset type from business_context or database.

        CRITICAL FIX: Resolves hardcoded "application" default (line 310).
        Enables asset-specific question routing:
        - Database assets → DatabaseQuestionsGenerator
        - Server assets → ServerQuestionsGenerator
        - Application assets → ApplicationQuestionsGenerator

        Priority order:
        1. business_context['asset_types'] dict (passed from caller)
        2. Database query (if db_session available via business_context)
        3. Fallback to "application" (safe default)

        Args:
            asset_id: Asset UUID as string
            business_context: Optional dict with asset_types mapping or db_session

        Returns:
            Asset type (e.g., "database", "server", "application") or "application" as safe fallback
        """
        # Check business_context first (most efficient)
        if business_context and "asset_types" in business_context:
            asset_types = business_context["asset_types"]
            if asset_id in asset_types:
                asset_type = asset_types[asset_id]
                logger.debug(
                    f"✅ Retrieved asset_type='{asset_type}' from business_context for {asset_id}"
                )
                return asset_type.lower()

        # Try database lookup if session available in business_context
        if business_context and "db_session" in business_context:
            try:
                from uuid import UUID
                from sqlalchemy import select
                from app.models.asset.models import Asset

                db_session = business_context["db_session"]
                asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id

                result = await db_session.execute(
                    select(Asset.asset_type).where(Asset.asset_id == asset_uuid)
                )
                row = result.scalar_one_or_none()

                if row:
                    logger.debug(
                        f"✅ Retrieved asset_type='{row}' from database for {asset_id}"
                    )
                    return row.lower()  # Ensure lowercase for consistency

            except Exception as e:
                logger.error(
                    f"Error fetching asset type from database for {asset_id}: {e}. "
                    "Using 'application' fallback",
                    exc_info=True,
                )

        # Fallback to "application" (safe default)
        logger.debug(f"⚠️ Using 'application' fallback for asset {asset_id}")
        return "application"
