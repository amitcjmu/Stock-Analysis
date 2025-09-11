"""
Asset Creation Commands

Handles asset creation operations from discovery data.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, select

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow

from .asset_base import AssetCommandsBase

logger = logging.getLogger(__name__)


class AssetCreationCommands(AssetCommandsBase):
    """Handles asset creation from discovery flows"""

    async def create_assets_from_discovery(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """Create multiple assets from discovery data"""
        created_assets = []

        # 🔧 CC FIX: Get master_flow_id and internal discovery flow ID from discovery flow before creating assets
        # This ensures assets have both discovery_flow_id AND master_flow_id set correctly
        master_flow_id, internal_discovery_flow_id = await self._get_master_flow_id(
            discovery_flow_id
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
                    discovery_flow_id=internal_discovery_flow_id,  # CRITICAL FIX: Use internal DB ID
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

    async def create_assets_from_discovery_no_commit(
        self,
        discovery_flow_id: uuid.UUID,
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory",
    ) -> List[Asset]:
        """
        Create multiple assets from discovery data without committing.

        This method is designed for use within larger atomic transactions
        where the caller manages the commit/rollback lifecycle.

        Args:
            discovery_flow_id: UUID of the discovery flow
            asset_data_list: List of asset data dictionaries
            discovered_in_phase: Phase where assets were discovered

        Returns:
            List of created Asset objects (not yet committed)
        """
        created_assets = []

        # Get master_flow_id and internal discovery flow ID from discovery flow before creating assets
        master_flow_id, internal_discovery_flow_id = await self._get_master_flow_id(
            discovery_flow_id
        )

        for asset_data in asset_data_list:
            try:
                # Extract asset information with improved field handling
                name = asset_data.get("name", f"Asset_{uuid.uuid4().hex[:8]}")
                asset_type = asset_data.get(
                    "asset_type", asset_data.get("type", "UNKNOWN")
                )

                # Handle SHA256 hashing for field mappings if present
                asset_hash = asset_data.get("asset_hash")
                if not asset_hash and asset_data.get("field_mappings"):
                    import hashlib

                    # Create deterministic hash from field mappings
                    mappings_str = str(sorted(asset_data["field_mappings"].items()))
                    asset_hash = hashlib.sha256(mappings_str.encode()).hexdigest()

                # Build comprehensive custom attributes
                custom_attributes = self._base_custom_attributes(
                    asset_data, discovered_in_phase
                )
                custom_attributes.update(
                    {
                        "discovery_flow_id": str(discovery_flow_id),
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                )

                # Add any additional custom attributes from input
                if "custom_attributes" in asset_data:
                    custom_attributes.update(asset_data["custom_attributes"])

                # Get normalized data for field mapping
                normalized_data = asset_data.get("normalized_data", {})

                # Create asset with comprehensive field mapping
                asset = Asset(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    name=name,
                    asset_name=name,
                    asset_type=asset_type,
                    status="discovered",
                    environment=normalized_data.get("environment", "Unknown"),
                    hostname=normalized_data.get("hostname"),
                    operating_system=normalized_data.get("operating_system"),
                    cpu_cores=normalized_data.get("cpu_cores"),
                    memory_gb=normalized_data.get("memory_gb"),
                    storage_gb=normalized_data.get("storage_gb"),
                    criticality=normalized_data.get("criticality", "Medium"),
                    application_name=normalized_data.get("application_name"),
                    six_r_strategy=normalized_data.get("six_r_strategy"),
                    migration_wave=normalized_data.get("migration_wave"),
                    discovery_flow_id=internal_discovery_flow_id,  # CRITICAL FIX: Use internal DB ID
                    master_flow_id=master_flow_id,
                    discovery_method="flow_based",
                    discovery_source="Discovery Flow",
                    discovery_timestamp=datetime.utcnow(),
                    raw_data=asset_data.get("raw_data", {}),
                    custom_attributes=custom_attributes,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Add optional asset hash if calculated
                if asset_hash:
                    asset.custom_attributes["asset_hash"] = asset_hash

                self.db.add(asset)
                created_assets.append(asset)

            except Exception as e:
                logger.error(f"Failed to create asset: {e}")
                continue

        logger.info(
            f"✅ Created {len(created_assets)} assets (no-commit) for flow {discovery_flow_id}"
        )

        return created_assets

    async def _get_master_flow_id(
        self, discovery_flow_id: uuid.UUID
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Get master_flow_id and internal discovery flow ID from discovery flow"""
        try:
            # CRITICAL FIX: Query by flow_id (external UUID) to get internal id and master_flow_id
            discovery_flow_query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id
                    == discovery_flow_id,  # Use flow_id for external UUID
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(discovery_flow_query)
            discovery_flow = result.scalar_one_or_none()

            if discovery_flow:
                master_flow_id = discovery_flow.master_flow_id
                internal_discovery_flow_id = discovery_flow.id  # Internal database ID
                logger.info(
                    f"✅ Found master_flow_id: {master_flow_id} and internal_id: "
                    f"{internal_discovery_flow_id} for flow_id: {discovery_flow_id}"
                )
                return master_flow_id, internal_discovery_flow_id

            logger.warning(
                f"⚠️ No discovery flow found for flow_id: {discovery_flow_id}"
            )
            return None, None

        except Exception as e:
            logger.error(
                f"❌ Failed to get flow data for discovery_flow_id {discovery_flow_id}: {e}"
            )
            return None, None
