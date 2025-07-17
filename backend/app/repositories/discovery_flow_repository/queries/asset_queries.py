"""
Asset Queries

Read operations for assets related to discovery flows.
"""

import uuid
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.asset import Asset

logger = logging.getLogger(__name__)


class AssetQueries:
    """Handles all asset query operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    async def get_assets_by_flow_id(self, discovery_flow_id: uuid.UUID) -> List[Asset]:
        """Get all assets created during a discovery flow"""
        # CC FIX: Query assets using the discovery_flow_id column, not custom_attributes
        stmt = select(Asset).where(
            and_(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
                Asset.discovery_flow_id == discovery_flow_id
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type with context filtering"""
        stmt = select(Asset).where(
            and_(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
                Asset.type == asset_type
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_discovered_assets(self) -> List[Asset]:
        """Get all assets with discovered status"""
        stmt = select(Asset).where(
            and_(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
                Asset.status == 'discovered'
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_assets_by_validation_status(self, validation_status: str) -> List[Asset]:
        """Get assets by validation status"""
        # Check validation_status in custom_attributes
        stmt = select(Asset).where(
            and_(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
                Asset.custom_attributes['validation_status'].astext == validation_status
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Optional[Asset]:
        """Get single asset by ID with context filtering"""
        stmt = select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def count_assets_by_flow_id(self, discovery_flow_id: uuid.UUID) -> int:
        """Count assets for a discovery flow"""
        from sqlalchemy import func
        
        stmt = select(func.count(Asset.id)).where(
            and_(
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
                Asset.discovery_flow_id == discovery_flow_id  # CC FIX: Use column field, not custom_attributes
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar() or 0