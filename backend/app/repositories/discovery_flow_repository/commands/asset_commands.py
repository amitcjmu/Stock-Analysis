"""
Asset Commands

Write operations for assets related to discovery flows.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..queries.asset_queries import AssetQueries

logger = logging.getLogger(__name__)


class AssetCommands:
    """Handles all asset write operations"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.asset_queries = AssetQueries(db, client_account_id, engagement_id)

    async def create_assets_from_discovery(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """Create multiple assets from discovery data"""
        created_assets = []

        # 🔧 CC FIX: Get master_flow_id from discovery flow before creating assets
        # This ensures assets have both discovery_flow_id AND master_flow_id set correctly
        master_flow_id = None
        try:
            discovery_flow_query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.id == discovery_flow_id,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(discovery_flow_query)
            discovery_flow = result.scalar_one_or_none()

            if discovery_flow and discovery_flow.master_flow_id:
                master_flow_id = discovery_flow.master_flow_id
                logger.info(
                    f"✅ Found master_flow_id: {master_flow_id} for discovery_flow_id: {discovery_flow_id}"
                )
            else:
                logger.warning(
                    f"⚠️ No master_flow_id found for discovery_flow_id: {discovery_flow_id}"
                )
        except Exception as e:
            logger.error(
                f"❌ Failed to get master_flow_id for discovery_flow_id {discovery_flow_id}: {e}"
            )

        for asset_data in asset_data_list:
            try:
                # Extract asset information
                name = asset_data.get("name", f"Asset_{uuid.uuid4().hex[:8]}")
                asset_type = asset_data.get("type", "UNKNOWN")

                # Build custom attributes with discovery metadata
                custom_attributes = {
                    "discovery_flow_id": str(discovery_flow_id),
                    "discovered_at": datetime.utcnow().isoformat(),
                    "discovered_in_phase": discovered_in_phase,  # 🔧 CC FIX: Track which phase discovered this asset
                    "discovery_method": "flow_based",
                    "raw_data": asset_data.get("raw_data", {}),
                    "normalized_data": asset_data.get("normalized_data", {}),
                    "confidence_score": asset_data.get("confidence_score", 0.0),
                    "validation_status": "pending",
                    "migration_ready": False,
                    "migration_complexity": asset_data.get(
                        "migration_complexity", "Unknown"
                    ),
                    "migration_priority": asset_data.get("migration_priority", 5),
                }

                # Add any additional custom attributes
                if "custom_attributes" in asset_data:
                    custom_attributes.update(asset_data["custom_attributes"])

                # Create asset with additional fields from normalized data
                normalized_data = asset_data.get("normalized_data", {})

                asset = Asset(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    name=name,
                    asset_name=name,  # Set asset_name same as name
                    asset_type=asset_type,  # Changed from 'type' to 'asset_type'
                    status="discovered",
                    environment=normalized_data.get(
                        "environment", custom_attributes.get("environment", "Unknown")
                    ),
                    hostname=normalized_data.get(
                        "hostname", custom_attributes.get("hostname")
                    ),
                    operating_system=normalized_data.get(
                        "operating_system", custom_attributes.get("operating_system")
                    ),
                    cpu_cores=normalized_data.get(
                        "cpu_cores", custom_attributes.get("cpu_cores")
                    ),
                    memory_gb=normalized_data.get(
                        "memory_gb", custom_attributes.get("memory_gb")
                    ),
                    storage_gb=normalized_data.get(
                        "storage_gb", custom_attributes.get("storage_gb")
                    ),
                    criticality=normalized_data.get(
                        "criticality", custom_attributes.get("criticality", "Medium")
                    ),
                    application_name=normalized_data.get(
                        "application_name", custom_attributes.get("application_name")
                    ),
                    six_r_strategy=normalized_data.get(
                        "six_r_strategy", custom_attributes.get("six_r_strategy")
                    ),
                    migration_wave=normalized_data.get(
                        "migration_wave", custom_attributes.get("migration_wave")
                    ),
                    discovery_flow_id=discovery_flow_id,  # Keep as UUID
                    master_flow_id=master_flow_id,  # 🔧 CC FIX: Set master_flow_id from discovery flow
                    discovery_method="flow_based",
                    discovery_source="Discovery Flow",
                    discovery_timestamp=datetime.utcnow(),
                    raw_data=asset_data.get("raw_data", {}),
                    custom_attributes=custom_attributes,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(asset)
                created_assets.append(asset)

            except Exception as e:
                logger.error(f"Failed to create asset: {e}")
                continue

        # Commit all assets
        if created_assets:
            await self.db.commit()

            # Refresh assets to get IDs
            for asset in created_assets:
                await self.db.refresh(asset)

            logger.info(
                f"✅ Created {len(created_assets)} assets for flow {discovery_flow_id}"
            )

        return created_assets

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
        self, asset_ids: List[uuid.UUID], migration_wave: Optional[str] = None
    ) -> int:
        """Mark assets as ready for migration"""
        try:
            updated_count = 0

            for asset_id in asset_ids:
                asset = await self.asset_queries.get_asset_by_id(asset_id)
                if asset:
                    custom_attrs = asset.custom_attributes or {}
                    custom_attrs["migration_ready"] = True
                    custom_attrs["migration_marked_at"] = datetime.utcnow().isoformat()

                    if migration_wave:
                        custom_attrs["migration_wave"] = migration_wave

                    stmt = (
                        update(Asset)
                        .where(Asset.id == asset_id)
                        .values(
                            custom_attributes=custom_attrs,
                            status="migration_ready",
                            updated_at=datetime.utcnow(),
                        )
                    )

                    await self.db.execute(stmt)
                    updated_count += 1

            await self.db.commit()
            logger.info(f"✅ Marked {updated_count} assets for migration")

            return updated_count

        except Exception as e:
            logger.error(f"Error marking assets for migration: {e}")
            await self.db.rollback()
            return 0
