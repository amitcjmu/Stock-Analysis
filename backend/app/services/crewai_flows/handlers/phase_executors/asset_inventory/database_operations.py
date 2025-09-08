"""
Asset Database Operations
Handles asset persistence, linking to raw records, and database interactions.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.data_import.core import RawImportRecord
from app.services.discovery_flow_service.managers.asset_manager import AssetManager

from .utils import AssetProcessingUtils

logger = logging.getLogger(__name__)


class AssetDatabaseOperations:
    """Handles database operations for asset inventory"""

    def __init__(self, state, flow_bridge=None):
        self.state = state
        self.flow_bridge = flow_bridge
        self.utils = AssetProcessingUtils()

    async def persist_assets_to_database(self, results: Dict[str, Any]):
        """Persist discovered assets to the database with deduplication"""
        try:
            logger.info("📦 Starting asset persistence to database")

            # Extract assets from results
            all_assets = []

            # Gather assets from different categories
            servers = results.get("servers", [])
            applications = results.get("applications", [])
            devices = results.get("devices", [])
            generic_assets = results.get("assets", [])

            # Combine all assets
            all_assets.extend(servers)
            all_assets.extend(applications)
            all_assets.extend(devices)
            all_assets.extend(generic_assets)

            if not all_assets:
                logger.warning("⚠️ No assets found to persist")
                return

            logger.info(f"📊 Found {len(all_assets)} assets to persist")

            # Note: Deduplication is handled by intelligent agents using deduplication tools
            # The inventory manager has instructions to avoid creating duplicates

            context = await self._get_context()
            if not context:
                logger.error("❌ No context available for asset persistence")
                return

            discovery_flow_id = await self._get_discovery_flow_id()
            if not discovery_flow_id:
                logger.error("❌ No discovery flow ID available for asset persistence")
                return

            logger.info(f"🔗 Using discovery flow ID: {discovery_flow_id}")

            async with AsyncSessionLocal() as db:
                asset_manager = AssetManager(db, context)

                # Get existing asset identifiers to prevent duplicates
                existing_assets = await self._get_existing_assets(db, context)
                existing_names = {row[0] for row in existing_assets if row[0]}
                existing_hostnames = {row[1] for row in existing_assets if row[1]}
                existing_ips = {row[2] for row in existing_assets if row[2]}

                logger.info(
                    f"📋 Found {len(existing_names)} existing asset names, "
                    f"{len(existing_hostnames)} hostnames, {len(existing_ips)} IPs in database"
                )

                # Prepare asset data for persistence
                asset_data_list = await self._prepare_asset_data_list(
                    all_assets, existing_names, existing_hostnames, existing_ips
                )

                # Create assets in database
                created_assets = await asset_manager.create_assets_from_discovery(
                    discovery_flow_id=discovery_flow_id,
                    asset_data_list=asset_data_list,
                    discovered_in_phase="inventory",
                )

                # SAFETY FIX: Check for empty created_assets to prevent downstream errors
                if not created_assets:
                    logger.warning(
                        "⚠️ No assets were created in database. This might indicate an issue with asset creation."
                    )
                    created_assets = []

                logger.info(
                    f"✅ Successfully persisted {len(created_assets)} assets to database"
                )

                # Link created assets back to raw import records
                await self._link_assets_to_raw_records(created_assets, asset_data_list)

                # Update state with created asset information
                await self._update_state_with_asset_info(created_assets)

        except Exception as e:
            logger.error(f"❌ Failed to persist assets to database: {e}", exc_info=True)

    async def _get_context(self) -> Optional[RequestContext]:
        """Get context from state or flow_bridge"""
        context = None
        if hasattr(self.state, "context"):
            context = self.state.context
        elif hasattr(self.state, "client_account_id") and hasattr(
            self.state, "engagement_id"
        ):
            # Build context from state
            context = RequestContext(
                client_account_id=self.state.client_account_id,
                engagement_id=self.state.engagement_id,
                user_id=getattr(self.state, "user_id", None),
                flow_id=getattr(self.state, "flow_id", None),
            )
        else:
            # Try to get context from flow_bridge if available
            if self.flow_bridge and hasattr(self.flow_bridge, "context"):
                context = self.flow_bridge.context
                logger.info(
                    f"🔄 Using context from flow_bridge: "
                    f"client={context.client_account_id}, "
                    f"engagement={context.engagement_id}"
                )

        if context:
            logger.info(
                f"📋 Using context: client={context.client_account_id}, engagement={context.engagement_id}"
            )

        return context

    async def _get_discovery_flow_id(self) -> Optional[uuid.UUID]:
        """Get discovery flow ID from state"""
        discovery_flow_id = None
        if hasattr(self.state, "discovery_flow_id"):
            discovery_flow_id = self.state.discovery_flow_id
        elif hasattr(self.state, "flow_internal_id"):
            discovery_flow_id = self.state.flow_internal_id
        elif hasattr(self.state, "flow_id"):
            discovery_flow_id = self.state.flow_id

        # 🔧 CC FIX: Convert discovery_flow_id to UUID if it's a string (Qodo Bot suggestion)
        if discovery_flow_id and isinstance(discovery_flow_id, str):
            try:
                discovery_flow_id = uuid.UUID(discovery_flow_id)
                logger.info(
                    f"🔧 Converted discovery_flow_id from string to UUID: {discovery_flow_id}"
                )
            except ValueError as e:
                logger.error(
                    f"❌ Invalid UUID format for discovery_flow_id: {discovery_flow_id} - {e}"
                )
                return None

        return discovery_flow_id

    async def _get_existing_assets(self, db, context: RequestContext):
        """Get existing asset identifiers to prevent duplicates"""
        existing_assets_query = select(
            Asset.name, Asset.hostname, Asset.ip_address
        ).where(
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        )
        existing_assets_result = await db.execute(existing_assets_query)
        return existing_assets_result.fetchall()

    async def _prepare_asset_data_list(
        self,
        all_assets: List[Dict],
        existing_names: set,
        existing_hostnames: set,
        existing_ips: set,
    ) -> List[Dict[str, Any]]:
        """Prepare asset data for persistence using field mappings"""
        field_mappings = getattr(self.state, "field_mappings", {})
        asset_data_list = []
        seen_names = set(existing_names)  # Start with existing names from database
        seen_hostnames = set(existing_hostnames)  # Track hostnames
        seen_ips = set(existing_ips)  # Track IP addresses

        for idx, asset in enumerate(all_assets):
            # Transform raw asset data using field mappings
            asset_name = self.utils.get_mapped_value(
                asset, "asset_name", field_mappings
            )
            hostname = self.utils.get_mapped_value(asset, "hostname", field_mappings)
            ip_address = self.utils.get_mapped_value(
                asset, "ip_address", field_mappings
            )

            # If no asset name, use hostname or IP as identifier, or leave blank
            if not asset_name or asset_name.strip() == "":
                if hostname:
                    asset_name = hostname
                elif ip_address:
                    asset_name = ip_address
                else:
                    # Leave blank for user to fill in manually
                    asset_name = ""

            # Generate unique asset name
            asset_name = self.utils.generate_unique_asset_name(
                asset_name, idx, seen_names
            )
            seen_names.add(asset_name)

            # Check for hostname conflicts and skip if duplicate
            if hostname and hostname in seen_hostnames:
                logger.warning(
                    f"⚠️ Skipping asset {idx + 1} - hostname '{hostname}' already exists"
                )
                continue
            elif hostname:
                seen_hostnames.add(hostname)

            # Check for IP conflicts and skip if duplicate
            if ip_address and ip_address in seen_ips:
                logger.warning(
                    f"⚠️ Skipping asset {idx + 1} - IP address '{ip_address}' already exists"
                )
                continue
            elif ip_address:
                seen_ips.add(ip_address)

            logger.debug(
                f"🏷️ Asset {idx + 1}: final_name='{asset_name}', hostname='{hostname}', ip='{ip_address}'"
            )

            asset_data = {
                "name": asset_name,
                "type": self.utils.determine_asset_type(asset, field_mappings),
                "raw_import_record_id": asset.get("raw_import_record_id"),
                "hostname": hostname,
                "ip_address": ip_address,
                "operating_system": self.utils.get_mapped_value(
                    asset, "operating_system", field_mappings
                ),
                "environment": self.utils.get_mapped_value(
                    asset, "environment", field_mappings
                )
                or "production",
                "criticality": self.utils.get_mapped_value(
                    asset, "criticality", field_mappings
                )
                or "medium",
                "status": "discovered",
                "application_name": self.utils.get_mapped_value(
                    asset, "application_name", field_mappings
                ),
                "cpu_cores": self.utils.parse_int(
                    self.utils.get_mapped_value(asset, "cpu_cores", field_mappings)
                ),
                "memory_gb": self.utils.parse_float(
                    self.utils.get_mapped_value(asset, "memory_gb", field_mappings)
                ),
                "storage_gb": self.utils.parse_float(
                    self.utils.get_mapped_value(asset, "storage_gb", field_mappings)
                ),
                "business_owner": self.utils.get_mapped_value(
                    asset, "business_owner", field_mappings
                ),
                "technical_owner": self.utils.get_mapped_value(
                    asset, "technical_owner", field_mappings
                ),
                "department": self.utils.get_mapped_value(
                    asset, "department", field_mappings
                ),
                "location": self.utils.get_mapped_value(
                    asset, "location", field_mappings
                ),
                "datacenter": self.utils.get_mapped_value(
                    asset, "datacenter", field_mappings
                ),
                "raw_data": asset,  # Store original data
                "field_mappings_used": field_mappings,
                "normalized_data": {  # Normalized data using field mappings
                    "hostname": hostname,
                    "ip_address": ip_address,
                    "operating_system": self.utils.get_mapped_value(
                        asset, "operating_system", field_mappings
                    ),
                    "environment": self.utils.get_mapped_value(
                        asset, "environment", field_mappings
                    )
                    or "production",
                    "criticality": self.utils.get_mapped_value(
                        asset, "criticality", field_mappings
                    )
                    or "medium",
                    "application_name": self.utils.get_mapped_value(
                        asset, "application_name", field_mappings
                    ),
                    "cpu_cores": self.utils.parse_int(
                        self.utils.get_mapped_value(asset, "cpu_cores", field_mappings)
                    ),
                    "memory_gb": self.utils.parse_float(
                        self.utils.get_mapped_value(asset, "memory_gb", field_mappings)
                    ),
                    "storage_gb": self.utils.parse_float(
                        self.utils.get_mapped_value(asset, "storage_gb", field_mappings)
                    ),
                },
            }
            asset_data_list.append(asset_data)

        return asset_data_list

    async def _link_assets_to_raw_records(
        self, created_assets: List, asset_data_list: List[Dict[str, Any]]
    ):
        """Link created assets back to their raw import records for full traceability"""
        try:
            async with AsyncSessionLocal() as session:
                linked_count = 0

                for i, (asset, asset_data) in enumerate(
                    zip(created_assets, asset_data_list)
                ):
                    raw_record_id = asset_data.get("raw_import_record_id")

                    if raw_record_id:
                        # Update the raw import record with the created asset ID
                        update_stmt = (
                            update(RawImportRecord)
                            .where(RawImportRecord.id == raw_record_id)
                            .values(
                                asset_id=asset.id,
                                is_processed=True,
                                processed_at=datetime.utcnow(),
                                processing_notes=f"Linked to asset: {asset.name} (ID: {asset.id})",
                            )
                        )

                        await session.execute(update_stmt)
                        linked_count += 1
                        logger.debug(
                            f"🔗 Linked asset {asset.name} to raw record {raw_record_id}"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Asset {asset.name} has no raw_import_record_id for linkage"
                        )

                await session.commit()
                logger.info(
                    f"✅ Successfully linked {linked_count}/{len(created_assets)} assets to raw import records"
                )

        except Exception as e:
            logger.error(
                f"❌ Failed to link assets to raw import records: {e}", exc_info=True
            )

    async def _update_state_with_asset_info(self, created_assets: List):
        """Update state with created asset information"""
        asset_ids = [str(asset.id) for asset in created_assets]

        # Update asset_inventory field with results
        if hasattr(self.state, "asset_inventory"):
            logger.info(
                f"🔍 Current asset_inventory type: {type(self.state.asset_inventory)}"
            )

            # Ensure asset_inventory is a dictionary, not a string
            if not isinstance(self.state.asset_inventory, dict):
                logger.info(
                    f"🔧 Converting asset_inventory from {type(self.state.asset_inventory)} to dict"
                )
                self.state.asset_inventory = {}

            self.state.asset_inventory["created_asset_ids"] = asset_ids
            self.state.asset_inventory["total_assets"] = len(created_assets)
            self.state.asset_inventory["status"] = "completed"
            self.state.asset_inventory["created_at"] = datetime.utcnow().isoformat()
            logger.info(f"✅ Updated asset_inventory: {self.state.asset_inventory}")
        else:
            # Initialize asset_inventory if it doesn't exist
            logger.info("🔧 Initializing asset_inventory (not found)")
            self.state.asset_inventory = {
                "created_asset_ids": asset_ids,
                "total_assets": len(created_assets),
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
            }

        # Also update asset_creation_results for backward compatibility
        if hasattr(self.state, "asset_creation_results"):
            # Ensure asset_creation_results is a dictionary
            if not isinstance(self.state.asset_creation_results, dict):
                self.state.asset_creation_results = {}

            self.state.asset_creation_results["created_asset_ids"] = asset_ids
            self.state.asset_creation_results["total_created"] = len(created_assets)
        else:
            # Initialize asset_creation_results if it doesn't exist
            self.state.asset_creation_results = {
                "created_asset_ids": asset_ids,
                "total_created": len(created_assets),
            }
