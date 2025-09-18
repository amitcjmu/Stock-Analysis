"""
Asset Creation Bridge Service
Converts discovery_assets to main assets table during inventory phase completion.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

# from app.models.discovery_asset import DiscoveryAsset  # Model removed - using Asset model instead
from app.models.asset import Asset, AssetStatus, AssetType
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class AssetCreationBridgeService:
    """
    Service for converting discovery assets to main asset inventory.
    Handles normalization, deduplication, and validation.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def create_assets_from_discovery(
        self, discovery_flow_id: uuid.UUID, user_id: uuid.UUID = None
    ) -> Dict[str, Any]:
        """
        Create assets in main inventory from discovery flow results.

        Args:
            discovery_flow_id: UUID of the discovery flow
            user_id: User performing the operation

        Returns:
            Dictionary with creation results and statistics
        """
        try:
            logger.info(
                f"🏗️ Starting asset creation from discovery flow: {discovery_flow_id}"
            )

            # Get discovery flow
            flow_query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == discovery_flow_id,
                    DiscoveryFlow.client_account_id == self.context.client_account_id,
                    DiscoveryFlow.engagement_id == self.context.engagement_id,
                )
            )
            flow_result = await self.db.execute(flow_query)
            discovery_flow = flow_result.scalar_one_or_none()

            if not discovery_flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")

            # Get discovery assets (using Asset model since DiscoveryAsset was removed)
            assets_query = select(Asset).where(
                and_(
                    Asset.discovery_flow_id == discovery_flow.id,
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                )
            )
            assets_result = await self.db.execute(assets_query)
            discovery_assets = assets_result.scalars().all()

            logger.info(f"📊 Found {len(discovery_assets)} discovery assets to process")

            # Process each discovery asset
            created_assets = []
            skipped_assets = []
            errors = []

            for discovery_asset in discovery_assets:
                try:
                    # Check for existing asset (deduplication)
                    existing_asset = await self._find_existing_asset(discovery_asset)

                    if existing_asset:
                        logger.info(
                            f"⚠️ Skipping duplicate asset: {discovery_asset.asset_name}"
                        )
                        skipped_assets.append(
                            {
                                "discovery_asset_id": str(discovery_asset.id),
                                "asset_name": discovery_asset.asset_name,
                                "reason": "duplicate",
                                "existing_asset_id": str(existing_asset.id),
                            }
                        )
                        continue

                    # Create new asset
                    new_asset = await self._create_asset_from_discovery(
                        discovery_asset, discovery_flow, user_id
                    )

                    if new_asset:
                        created_assets.append(new_asset)
                        logger.info(
                            f"✅ Created asset: {new_asset.name} (ID: {new_asset.id})"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ Failed to process discovery asset {discovery_asset.id}: {e}"
                    )
                    errors.append(
                        {
                            "discovery_asset_id": str(discovery_asset.id),
                            "asset_name": discovery_asset.asset_name,
                            "error": str(e),
                        }
                    )

            # Commit all changes
            await self.db.commit()

            # Update discovery flow with asset creation results
            await self._update_discovery_flow_completion(
                discovery_flow, created_assets, skipped_assets, errors
            )

            result = {
                "success": True,
                "discovery_flow_id": discovery_flow_id,
                "statistics": {
                    "total_discovery_assets": len(discovery_assets),
                    "assets_created": len(created_assets),
                    "assets_skipped": len(skipped_assets),
                    "errors": len(errors),
                },
                "created_assets": [str(asset.id) for asset in created_assets],
                "skipped_assets": skipped_assets,
                "errors": errors,
                "completed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"🎯 Asset creation completed: {result['statistics']}")
            return result

        except Exception as e:
            logger.error(f"❌ Asset creation bridge failed: {e}")
            await self.db.rollback()
            raise

    async def _find_existing_asset(self, discovery_asset: Asset) -> Optional[Asset]:
        """
        Find existing asset to avoid duplicates.
        Uses business rules for deduplication.
        """
        # Primary deduplication by name and type within engagement
        query = select(Asset).where(
            and_(
                Asset.name == discovery_asset.asset_name,
                Asset.asset_type == self._map_asset_type(discovery_asset.asset_type),
                Asset.client_account_id == self.context.client_account_id,
                Asset.engagement_id == self.context.engagement_id,
            )
        )

        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Secondary deduplication by hostname/IP if available
        normalized_data = discovery_asset.normalized_data or {}
        hostname = normalized_data.get("hostname") or normalized_data.get("fqdn")
        ip_address = normalized_data.get("ip_address")

        if hostname or ip_address:
            conditions = [
                Asset.client_account_id == self.context.client_account_id,
                Asset.engagement_id == self.context.engagement_id,
            ]

            if hostname:
                conditions.append(Asset.hostname == hostname)
            if ip_address:
                conditions.append(Asset.ip_address == ip_address)

            query = select(Asset).where(and_(*conditions))
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        return None

    async def _create_asset_from_discovery(
        self,
        discovery_asset: Asset,
        discovery_flow: DiscoveryFlow,
        user_id: uuid.UUID = None,
    ) -> Asset:
        """
        Create a new Asset from DiscoveryAsset with proper normalization.
        """
        # Extract normalized data
        raw_data = discovery_asset.raw_data or {}
        normalized_data = discovery_asset.normalized_data or {}

        # Map asset type
        asset_type = self._map_asset_type(discovery_asset.asset_type)

        # Create new asset
        new_asset = Asset(
            # Multi-tenant isolation
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            # Basic information
            name=discovery_asset.asset_name,
            asset_name=discovery_asset.asset_name,
            asset_type=asset_type,
            description=normalized_data.get("description")
            or f"Discovered via {discovery_asset.discovery_method}",
            # Network information
            hostname=normalized_data.get("hostname"),
            fqdn=normalized_data.get("fqdn"),
            ip_address=normalized_data.get("ip_address"),
            mac_address=normalized_data.get("mac_address"),
            # Environment and location
            environment=normalized_data.get("environment", "Unknown"),
            location=normalized_data.get("location"),
            datacenter=normalized_data.get("datacenter"),
            # Technical specifications
            operating_system=normalized_data.get("operating_system"),
            os_version=(
                str(normalized_data.get("os_version"))
                if normalized_data.get("os_version") is not None
                else None
            ),
            cpu_cores=self._safe_int(normalized_data.get("cpu_cores")),
            memory_gb=self._safe_float(normalized_data.get("memory_gb")),
            storage_gb=self._safe_float(normalized_data.get("storage_gb")),
            # Business information
            business_owner=normalized_data.get("business_owner"),
            technical_owner=normalized_data.get("technical_owner"),
            department=normalized_data.get("department"),
            application_name=normalized_data.get("application_name"),
            technology_stack=normalized_data.get("technology_stack"),
            criticality=normalized_data.get("criticality", "Medium"),
            business_criticality=normalized_data.get("business_criticality", "Medium"),
            # Migration assessment from discovery
            migration_priority=discovery_asset.migration_priority or 5,
            migration_complexity=discovery_asset.migration_complexity,
            migration_status=(
                AssetStatus.ASSESSED
                if discovery_asset.migration_ready
                else AssetStatus.DISCOVERED
            ),
            # Discovery metadata
            discovery_method=discovery_asset.discovery_method or "discovery_flow",
            discovery_source=f"Discovery Flow {discovery_flow.flow_name}",
            discovery_timestamp=discovery_asset.created_at,
            # Data preservation
            raw_data=raw_data,
            custom_attributes={
                "discovery_flow_id": str(discovery_flow.id),
                "discovery_asset_id": str(discovery_asset.id),
                "discovered_in_phase": discovery_asset.discovered_in_phase,
                "confidence_score": discovery_asset.confidence_score,
                "validation_status": discovery_asset.validation_status,
            },
            # Audit information
            imported_by=None,  # Don't set foreign key references that might not exist
            imported_at=datetime.utcnow(),
            created_by=None,  # Don't set foreign key references that might not exist
            is_mock=discovery_asset.is_mock,
        )

        # Add to session
        self.db.add(new_asset)
        await self.db.flush()  # Get the ID

        return new_asset

    def _map_asset_type(self, discovery_type: str) -> AssetType:
        """
        Map discovery asset type to main Asset model enum.
        """
        if not discovery_type:
            return AssetType.OTHER

        # Normalize the type string
        discovery_type = discovery_type.lower().strip()

        # Mapping logic
        type_mapping = {
            "server": AssetType.SERVER,
            "web_server": AssetType.SERVER,
            "app_server": AssetType.SERVER,
            "application_server": AssetType.SERVER,
            "database": AssetType.DATABASE,
            "database_server": AssetType.DATABASE,
            "db_server": AssetType.DATABASE,
            "application": AssetType.APPLICATION,
            "app": AssetType.APPLICATION,
            "web_application": AssetType.APPLICATION,
            "network": AssetType.NETWORK,
            "network_device": AssetType.NETWORK,
            "load_balancer": AssetType.LOAD_BALANCER,
            "storage": AssetType.STORAGE,
            "storage_device": AssetType.STORAGE,
            "virtual_machine": AssetType.VIRTUAL_MACHINE,
            "vm": AssetType.VIRTUAL_MACHINE,
            "container": AssetType.CONTAINER,
            "security_group": AssetType.SECURITY_GROUP,
        }

        return type_mapping.get(discovery_type, AssetType.OTHER)

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer."""
        if value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_string(self, value: Any) -> Optional[str]:
        """Safely convert value to string."""
        if value is None:
            return None
        try:
            return str(value)
        except (ValueError, TypeError):
            return None

    async def _update_discovery_flow_completion(
        self,
        discovery_flow: DiscoveryFlow,
        created_assets: List[Asset],
        skipped_assets: List[Dict],
        errors: List[Dict],
    ):
        """
        Update discovery flow with asset creation completion data.
        """
        # Update flow progress and status
        discovery_flow.asset_inventory_completed = True
        discovery_flow.update_progress()  # Recalculate progress based on completed phases

        # Store asset creation results in crewai_state_data
        asset_creation_results = {
            "assets_created": len(created_assets),
            "assets_skipped": len(skipped_assets),
            "errors": len(errors),
            "created_asset_ids": [str(asset.id) for asset in created_assets],
            "skipped_details": skipped_assets,
            "error_details": errors,
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Update crewai_state_data with asset creation results
        state_data = discovery_flow.crewai_state_data or {}
        state_data["asset_creation_bridge"] = asset_creation_results
        state_data["inventory_phase_completed"] = True
        state_data["next_phase"] = (
            "dependencies" if len(created_assets) > 0 else "completed"
        )

        discovery_flow.crewai_state_data = state_data

        await self.db.commit()

        logger.info(
            f"📊 Updated discovery flow {discovery_flow.flow_id} with asset creation results"
        )
