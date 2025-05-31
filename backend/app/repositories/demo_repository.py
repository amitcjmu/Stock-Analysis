"""
Demo Repository
Context-aware repository for accessing mock/demo data with multi-tenant support.
"""

import logging
from typing import List, Dict, Optional, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cmdb_asset import CMDBAsset, MigrationWave
from app.models.sixr_analysis import SixRAnalysis
from app.models.tags import Tag, AssetTag
from app.models.client_account import ClientAccount
from app.repositories.base import ContextAwareRepository

logger = logging.getLogger(__name__)

class DemoRepository(ContextAwareRepository):
    """Repository for demo/mock data operations with context awareness."""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[int] = None, engagement_id: Optional[int] = None):
        super().__init__(db, client_account_id, engagement_id)
    
    async def get_demo_assets(
        self, 
        limit: int = 100, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CMDBAsset]:
        """Get demo assets with optional filtering."""
        stmt = select(CMDBAsset).where(CMDBAsset.is_mock == True)
        
        # Apply context filtering
        stmt = self._apply_context_filter_stmt(stmt, CMDBAsset)
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(CMDBAsset, key) and value is not None:
                    stmt = stmt.where(getattr(CMDBAsset, key) == value)
        
        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_demo_asset_by_id(self, asset_id: str) -> Optional[CMDBAsset]:
        """Get a specific demo asset by ID."""
        stmt = select(CMDBAsset).where(
            and_(
                CMDBAsset.id == asset_id,
                CMDBAsset.is_mock == True
            )
        )
        
        # Apply context filtering
        stmt = self._apply_context_filter_stmt(stmt, CMDBAsset)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_demo_asset(self, asset_data: Dict[str, Any]) -> CMDBAsset:
        """Create a new demo asset."""
        # Ensure it's marked as mock data
        asset_data['is_mock'] = True
        
        # Set context if available
        if self.client_account_id:
            asset_data['client_account_id'] = self.client_account_id
        if self.engagement_id:
            asset_data['engagement_id'] = self.engagement_id
        
        asset = CMDBAsset(**asset_data)
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        
        logger.info(f"Created demo asset: {asset.name} (ID: {asset.id})")
        return asset
    
    async def update_demo_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> Optional[CMDBAsset]:
        """Update an existing demo asset."""
        asset = await self.get_demo_asset_by_id(asset_id)
        if not asset:
            return None
        
        # Update fields
        for key, value in asset_data.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        await self.db.commit()
        await self.db.refresh(asset)
        
        logger.info(f"Updated demo asset: {asset.name} (ID: {asset.id})")
        return asset
    
    async def delete_demo_asset(self, asset_id: str) -> bool:
        """Delete a demo asset."""
        asset = await self.get_demo_asset_by_id(asset_id)
        if not asset:
            return False
        
        await self.db.delete(asset)
        await self.db.commit()
        
        logger.info(f"Deleted demo asset: {asset.name} (ID: {asset_id})")
        return True
    
    async def get_demo_assets_summary(self) -> Dict[str, Any]:
        """Get summary statistics for demo assets."""
        # Total assets count
        count_stmt = select(func.count(CMDBAsset.id)).where(CMDBAsset.is_mock == True)
        count_stmt = self._apply_context_filter_stmt(count_stmt, CMDBAsset)
        
        result = await self.db.execute(count_stmt)
        total_assets = result.scalar()
        
        # Asset type distribution
        type_stmt = select(
            CMDBAsset.asset_type,
            func.count(CMDBAsset.id).label('count')
        ).where(CMDBAsset.is_mock == True).group_by(CMDBAsset.asset_type)
        
        type_stmt = self._apply_context_filter_stmt(type_stmt, CMDBAsset)
        
        result = await self.db.execute(type_stmt)
        asset_types = {row.asset_type: row.count for row in result}
        
        # Environment distribution
        env_stmt = select(
            CMDBAsset.environment,
            func.count(CMDBAsset.id).label('count')
        ).where(CMDBAsset.is_mock == True).group_by(CMDBAsset.environment)
        
        env_stmt = self._apply_context_filter_stmt(env_stmt, CMDBAsset)
        
        result = await self.db.execute(env_stmt)
        environments = {row.environment: row.count for row in result}
        
        # Business criticality distribution
        criticality_stmt = select(
            CMDBAsset.criticality,
            func.count(CMDBAsset.id).label('count')
        ).where(CMDBAsset.is_mock == True).group_by(CMDBAsset.criticality)
        
        criticality_stmt = self._apply_context_filter_stmt(criticality_stmt, CMDBAsset)
        
        result = await self.db.execute(criticality_stmt)
        business_criticality = {row.criticality: row.count for row in result}
        
        # Total resource calculations
        resource_stmt = select(
            func.sum(CMDBAsset.cpu_cores).label('total_cpu'),
            func.sum(CMDBAsset.memory_gb).label('total_memory'),
            func.sum(CMDBAsset.storage_gb).label('total_storage')
        ).where(CMDBAsset.is_mock == True)
        
        resource_stmt = self._apply_context_filter_stmt(resource_stmt, CMDBAsset)
        
        result = await self.db.execute(resource_stmt)
        resources = result.first()
        
        return {
            "total_assets": total_assets,
            "asset_types": asset_types,
            "environments": environments,
            "business_criticality": business_criticality,
            "total_resources": {
                "cpu_cores": resources.total_cpu or 0,
                "memory_gb": resources.total_memory or 0,
                "storage_gb": resources.total_storage or 0
            }
        }
    
    async def get_demo_analyses(
        self, 
        limit: int = 50, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SixRAnalysis]:
        """Get demo 6R analyses."""
        stmt = select(SixRAnalysis)
        
        # Apply context filtering
        stmt = self._apply_context_filter_stmt(stmt, SixRAnalysis)
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(SixRAnalysis, key) and value is not None:
                    stmt = stmt.where(getattr(SixRAnalysis, key) == value)
        
        # Order by creation date (newest first)
        stmt = stmt.order_by(desc(SixRAnalysis.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_demo_waves(self) -> List[MigrationWave]:
        """Get demo migration waves."""
        stmt = select(MigrationWave).where(MigrationWave.is_mock == True)
        
        # Apply context filtering
        stmt = self._apply_context_filter_stmt(stmt, MigrationWave)
        
        # Order by wave number
        stmt = stmt.order_by(MigrationWave.wave_number)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_demo_tags(self, filters: Optional[Dict[str, Any]] = None) -> List[Tag]:
        """Get demo tags."""
        stmt = select(Tag)
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(Tag, key) and value is not None:
                    stmt = stmt.where(getattr(Tag, key) == value)
        
        # Order by category, then name
        stmt = stmt.order_by(Tag.category, Tag.name)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    def _apply_context_filter_stmt(self, stmt, model):
        """Apply context filtering to a select statement."""
        if self.client_account_id and hasattr(model, 'client_account_id'):
            stmt = stmt.where(model.client_account_id == self.client_account_id)
        if self.engagement_id and hasattr(model, 'engagement_id'):
            stmt = stmt.where(model.engagement_id == self.engagement_id)
        return stmt
    
    async def get_demo_engagement_info(self) -> Dict[str, Any]:
        """Get demo engagement information."""
        if not self.client_account_id:
            return {
                "client_name": "Demo Corporation",
                "engagement_name": "Cloud Migration Assessment",
                "engagement_type": "Migration Planning",
                "start_date": "2025-05-01",
                "estimated_end_date": "2025-08-31",
                "project_manager": "Sarah Johnson",
                "technical_lead": "Michael Chen",
                "total_assets_discovered": 10,
                "assessment_phase": "Discovery Complete",
                "next_milestone": "6R Analysis",
                "confidence_level": "High"
            }
        
        # Get client account info
        client_stmt = select(ClientAccount).where(ClientAccount.id == self.client_account_id)
        result = await self.db.execute(client_stmt)
        client = result.scalar_one_or_none()
        
        # Get asset count
        count_stmt = select(func.count(CMDBAsset.id)).where(
            and_(
                CMDBAsset.client_account_id == self.client_account_id,
                CMDBAsset.is_mock == True
            )
        )
        
        if self.engagement_id:
            count_stmt = count_stmt.where(CMDBAsset.engagement_id == self.engagement_id)
        
        result = await self.db.execute(count_stmt)
        assets_count = result.scalar()
        
        return {
            "client_name": client.name if client else "Demo Corporation",
            "engagement_name": "Cloud Migration Assessment",
            "engagement_type": "Migration Planning",
            "start_date": "2025-05-01",
            "estimated_end_date": "2025-08-31",
            "project_manager": "Sarah Johnson",
            "technical_lead": "Michael Chen",
            "total_assets_discovered": assets_count,
            "assessment_phase": "Discovery Complete",
            "next_milestone": "6R Analysis",
            "confidence_level": "High"
        } 