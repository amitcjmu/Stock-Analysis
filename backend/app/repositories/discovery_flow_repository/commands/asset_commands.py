"""
Asset Commands

Unified asset commands facade maintaining backward compatibility.
Modularized for better maintainability while preserving existing API.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset

from .asset_commands.asset_base import AssetCommandsBase
from .asset_commands.asset_creation import AssetCreationCommands
from .asset_commands.asset_updates import AssetUpdateCommands
from .asset_commands.asset_utils import AssetUtilityCommands


class AssetCommands(AssetCommandsBase):
    """Unified asset commands class maintaining backward compatibility"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        super().__init__(db, client_account_id, engagement_id)

        # Initialize command modules as attributes
        self._creation = AssetCreationCommands(db, client_account_id, engagement_id)
        self._updates = AssetUpdateCommands(db, client_account_id, engagement_id)
        self._utils = AssetUtilityCommands(db, client_account_id, engagement_id)

    # Asset creation methods - delegate to creation module
    async def create_assets_from_discovery(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """Create multiple assets from discovery data"""
        return await self._creation.create_assets_from_discovery(
            discovery_flow_id, asset_data_list, discovered_in_phase
        )

    async def create_assets_from_discovery_no_commit(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """Create multiple assets from discovery data without committing"""
        return await self._creation.create_assets_from_discovery_no_commit(
            discovery_flow_id, asset_data_list, discovered_in_phase
        )

    # Asset update methods - delegate to updates module
    async def update_asset_validation(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_notes: Optional[str] = None,
    ) -> Optional[Asset]:
        """Update asset validation status"""
        return await self._updates.update_asset_validation(
            asset_id, validation_status, validation_notes
        )

    async def bulk_update_assets(
        self, discovery_flow_id: uuid.UUID, updates: Dict[str, Any]
    ) -> int:
        """Bulk update assets for a discovery flow"""
        return await self._updates.bulk_update_assets(discovery_flow_id, updates)

    async def mark_assets_for_migration(
        self, discovery_flow_id: uuid.UUID, asset_ids: Optional[list] = None
    ) -> int:
        """Mark assets as ready for migration"""
        return await self._updates.mark_assets_for_migration(
            discovery_flow_id, asset_ids
        )

    # Utility methods - delegate to utils module
    async def _get_master_flow_id(
        self, discovery_flow_id: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """Get master flow ID from discovery flow - backward compatibility method"""
        return await self._utils.get_master_flow_id_from_discovery(discovery_flow_id)
