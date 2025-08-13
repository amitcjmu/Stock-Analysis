"""
Asset Service

Provides controlled asset creation and management through proper repository pattern.
This service ensures multi-tenant isolation, transactional integrity, and idempotency.

CC: Service layer for asset operations following repository pattern
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.asset import Asset, AssetStatus
from app.repositories.asset_repository import AssetRepository

logger = logging.getLogger(__name__)


class AssetService:
    """Service for controlled asset operations"""

    def __init__(self, db: AsyncSession, context_info: Dict[str, Any]):
        """
        Initialize asset service with database session and context

        Args:
            db: Database session from orchestrator
            context_info: Tenant context information
        """
        self.db = db
        self.context_info = context_info
        self.repository = AssetRepository(db)

    async def create_asset(self, asset_data: Dict[str, Any]) -> Optional[Asset]:
        """
        Create an asset with proper validation and idempotency

        Args:
            asset_data: Asset information to create

        Returns:
            Created asset or existing asset if duplicate
        """
        try:
            # Extract context IDs - handle both string and UUID types
            client_id = self._get_uuid(
                asset_data.get("client_account_id")
                or self.context_info.get("client_account_id")
            )
            engagement_id = self._get_uuid(
                asset_data.get("engagement_id")
                or self.context_info.get("engagement_id")
            )

            if not client_id or not engagement_id:
                raise ValueError(
                    "Missing required tenant context (client_id, engagement_id)"
                )

            # Check for existing asset (idempotency)
            existing = await self._find_existing_asset(
                name=asset_data.get("name"),
                client_id=client_id,
                engagement_id=engagement_id,
            )

            if existing:
                logger.info(
                    f"Asset already exists: {existing.name} (ID: {existing.id})"
                )
                return existing

            # Build new asset
            new_asset = Asset(
                # Multi-tenant context - no double UUID conversion
                client_account_id=client_id,
                engagement_id=engagement_id,
                # Basic information
                name=asset_data.get("name", "Unknown Asset"),
                asset_name=asset_data.get("name", "Unknown Asset"),
                asset_type=asset_data.get("asset_type", "Unknown"),
                description=asset_data.get("description", "Discovered by agent"),
                # Network information
                hostname=asset_data.get("hostname"),
                ip_address=asset_data.get("ip_address"),
                # Environment
                environment=asset_data.get("environment", "Unknown"),
                # Technical specifications
                operating_system=asset_data.get("operating_system"),
                cpu_cores=asset_data.get("cpu_cores"),
                memory_gb=asset_data.get("memory_gb"),
                storage_gb=asset_data.get("storage_gb"),
                # Business information
                business_unit=asset_data.get("business_unit"),
                owner=asset_data.get("owner"),
                criticality=asset_data.get("criticality", "Medium"),
                # Status
                status=AssetStatus.DISCOVERED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                # Store full attributes as JSON
                attributes=asset_data.get("attributes", {}),
            )

            # Use repository for controlled creation
            created_asset = await self.repository.create(new_asset)

            logger.info(
                f"✅ Asset created via service: {created_asset.name} (ID: {created_asset.id})"
            )
            return created_asset

        except Exception as e:
            logger.error(f"❌ Asset service failed to create asset: {e}")
            raise

    async def _find_existing_asset(
        self, name: str, client_id: uuid.UUID, engagement_id: uuid.UUID
    ) -> Optional[Asset]:
        """Check for existing asset with same name in same context"""
        try:
            stmt = select(Asset).where(
                and_(
                    Asset.name == name,
                    Asset.client_account_id == client_id,
                    Asset.engagement_id == engagement_id,
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to check for existing asset: {e}")
            return None

    def _get_uuid(self, value: Any) -> Optional[uuid.UUID]:
        """
        Safely convert value to UUID

        Args:
            value: String UUID, UUID object, or None

        Returns:
            UUID object or None
        """
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return value

        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid UUID value: {value}")
            return None

    async def bulk_create_assets(
        self, assets_data: List[Dict[str, Any]]
    ) -> List[Asset]:
        """
        Create multiple assets in a single transaction

        Args:
            assets_data: List of asset data dictionaries

        Returns:
            List of created assets
        """
        created_assets = []

        try:
            for asset_data in assets_data:
                asset = await self.create_asset(asset_data)
                if asset:
                    created_assets.append(asset)

            # Commit all in single transaction
            await self.db.commit()

            logger.info(f"✅ Bulk created {len(created_assets)} assets")
            return created_assets

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Bulk asset creation failed: {e}")
            raise
