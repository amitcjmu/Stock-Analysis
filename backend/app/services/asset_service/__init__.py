"""
Asset Service Package

Modularized asset service for controlled asset creation and management.
Maintains backward compatibility - existing imports will continue to work:
    from app.services.asset_service import AssetService

CC: Service layer for asset operations following repository pattern
"""

from .base import AssetService as _AssetServiceBase
from .deduplication import create_or_update_asset
from .operations import create_asset, bulk_create_assets, legacy_create_asset


class AssetService(_AssetServiceBase):
    """
    Complete AssetService with all operations.

    This class combines base initialization with all operational methods
    to maintain the same interface as the original monolithic file.
    """

    async def create_or_update_asset(self, *args, **kwargs):
        """Unified asset creation with hierarchical deduplication"""
        return await create_or_update_asset(self, *args, **kwargs)

    async def create_asset(self, *args, **kwargs):
        """DEPRECATED: Use create_or_update_asset() instead"""
        return await create_asset(self, *args, **kwargs)

    async def bulk_create_assets(self, *args, **kwargs):
        """Create multiple assets without committing"""
        return await bulk_create_assets(self, *args, **kwargs)

    async def _legacy_create_asset(self, *args, **kwargs):
        """Original create_asset implementation - kept for reference only"""
        return await legacy_create_asset(self, *args, **kwargs)

    # Helper methods from helpers module (accessed via service instance)
    def _get_smart_asset_name(self, data):
        """Generate unique asset name from available data"""
        from .helpers import get_smart_asset_name

        return get_smart_asset_name(data)

    def _safe_int_convert(self, value, default=None):
        """Convert value to integer with safe error handling"""
        from .helpers import safe_int_convert

        return safe_int_convert(value, default)

    def _safe_float_convert(self, value, default=None):
        """Convert value to float with safe error handling"""
        from .helpers import safe_float_convert

        return safe_float_convert(value, default)

    def _convert_numeric_fields(self, asset_data):
        """Convert all numeric fields with proper error handling"""
        from .helpers import convert_numeric_fields

        return convert_numeric_fields(asset_data)

    # Deduplication methods (already async, just reference)
    async def _find_existing_asset_hierarchical(self, *args, **kwargs):
        """Hierarchical deduplication check"""
        from .deduplication import find_existing_asset_hierarchical

        return await find_existing_asset_hierarchical(self, *args, **kwargs)

    async def _create_new_asset(self, *args, **kwargs):
        """Create a new asset"""
        from .deduplication import create_new_asset

        return await create_new_asset(self, *args, **kwargs)

    async def _enrich_asset(self, *args, **kwargs):
        """Non-destructive enrichment"""
        from .deduplication import enrich_asset

        return await enrich_asset(self, *args, **kwargs)

    async def _overwrite_asset(self, *args, **kwargs):
        """Explicit overwrite"""
        from .deduplication import overwrite_asset

        return await overwrite_asset(self, *args, **kwargs)

    async def _find_existing_asset(self, *args, **kwargs):
        """Check for existing asset with same name"""
        from .operations import find_existing_asset

        return await find_existing_asset(self, *args, **kwargs)


# Export for backward compatibility
__all__ = ["AssetService"]
