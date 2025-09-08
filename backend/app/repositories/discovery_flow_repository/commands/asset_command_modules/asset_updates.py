"""
Asset Update Commands

Handles asset update operations including validation and bulk updates.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, update

from app.models.asset import Asset

from .asset_base import AssetCommandsBase

logger = logging.getLogger(__name__)


class AssetUpdateCommands(AssetCommandsBase):
    """Handles asset update operations"""

    async def update_asset_validation(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_notes: Optional[str] = None,
    ) -> Optional[Asset]:
        """Update asset validation status"""
        try:
            # Get existing asset
            asset = await self.asset_queries.get_asset_by_id(asset_id)
            if not asset:
                logger.warning(f"Asset not found: {asset_id}")
                return None

            # Update custom attributes
            custom_attrs = asset.custom_attributes or {}
            custom_attrs["validation_status"] = validation_status
            custom_attrs["validation_timestamp"] = datetime.utcnow().isoformat()

            if validation_notes:
                custom_attrs["validation_notes"] = validation_notes

            # Determine if asset is migration ready based on validation
            if validation_status == "approved":
                custom_attrs["migration_ready"] = True
                asset.status = "validated"
            elif validation_status == "rejected":
                custom_attrs["migration_ready"] = False
                asset.status = "rejected"

            # Update asset
            stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                    )
                )
                .values(
                    custom_attributes=custom_attrs,
                    status=asset.status,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            # Return updated asset
            return await self.asset_queries.get_asset_by_id(asset_id)

        except Exception as e:
            logger.error(f"Error updating asset validation: {e}")
            await self.db.rollback()
            return None

    async def bulk_update_assets(
        self, discovery_flow_id: uuid.UUID, updates: Dict[str, Any]
    ) -> int:
        """Bulk update assets for a discovery flow"""
        try:
            # Build update values
            update_values = {"updated_at": datetime.utcnow()}

            # Handle status updates
            if "status" in updates:
                update_values["status"] = updates["status"]

            # Handle custom attribute updates
            if "custom_attributes" in updates:
                # This requires special handling for JSONB updates
                # For now, we'll need to fetch and update individually
                assets = await self.asset_queries.get_assets_by_flow_id(
                    discovery_flow_id
                )

                updated_count = 0
                for asset in assets:
                    custom_attrs = asset.custom_attributes or {}
                    custom_attrs.update(updates["custom_attributes"])

                    stmt = (
                        update(Asset)
                        .where(Asset.id == asset.id)
                        .values(
                            custom_attributes=custom_attrs, updated_at=datetime.utcnow()
                        )
                    )

                    await self.db.execute(stmt)
                    updated_count += 1

                await self.db.commit()
                return updated_count

            # For simple updates without custom attributes
            stmt = (
                update(Asset)
                .where(
                    and_(
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                        Asset.discovery_flow_id
                        == discovery_flow_id,  # CC FIX: Use column field, not custom_attributes
                    )
                )
                .values(**update_values)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount

        except Exception as e:
            logger.error(f"Error in bulk asset update: {e}")
            await self.db.rollback()
            return 0

    async def mark_assets_for_migration(
        self, discovery_flow_id: uuid.UUID, asset_ids: Optional[list] = None
    ) -> int:
        """Mark assets as ready for migration"""
        try:
            # Get assets to update
            assets_to_update = await self.asset_queries.get_assets_by_flow_id(
                discovery_flow_id
            )

            if asset_ids:
                assets_to_update = [
                    asset for asset in assets_to_update if asset.id in asset_ids
                ]

            updated_count = 0
            for asset in assets_to_update:
                custom_attrs = asset.custom_attributes or {}
                custom_attrs["migration_ready"] = True
                custom_attrs["migration_marked_at"] = datetime.utcnow().isoformat()

                asset_stmt = (
                    update(Asset)
                    .where(Asset.id == asset.id)
                    .values(
                        custom_attributes=custom_attrs,
                        status="migration_ready",
                        updated_at=datetime.utcnow(),
                    )
                )

                await self.db.execute(asset_stmt)
                updated_count += 1

            await self.db.commit()

            logger.info(
                f"✅ Marked {updated_count} assets for migration in flow {discovery_flow_id}"
            )

            return updated_count

        except Exception as e:
            logger.error(f"Error marking assets for migration: {e}")
            await self.db.rollback()
            return 0
