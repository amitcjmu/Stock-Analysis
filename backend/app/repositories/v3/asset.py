"""
V3 Asset Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, or_
from app.repositories.v3.base import V3BaseRepository
from app.models import Asset
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class V3AssetRepository(V3BaseRepository[Asset]):
    """Repository for V3 assets using consolidated Asset model"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        super().__init__(db, Asset, client_account_id, engagement_id)
    
    async def get_by_discovery_flow(self, discovery_flow_id: str) -> List[Asset]:
        """Get all assets for a discovery flow"""
        query = select(Asset).where(
            Asset.discovery_flow_id == discovery_flow_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_master_flow(self, master_flow_id: str) -> List[Asset]:
        """Get all assets for a master flow"""
        query = select(Asset).where(
            Asset.master_flow_id == master_flow_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Get asset by hostname"""
        query = select(Asset).where(
            Asset.hostname == hostname
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_ip_address(self, ip_address: str) -> Optional[Asset]:
        """Get asset by IP address"""
        query = select(Asset).where(
            Asset.ip_address == ip_address
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_assets(
        self,
        search_term: str,
        asset_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Asset]:
        """Search assets by name, hostname, or IP"""
        query = select(Asset).where(
            or_(
                Asset.asset_name.ilike(f"%{search_term}%"),
                Asset.hostname.ilike(f"%{search_term}%"),
                Asset.ip_address.ilike(f"%{search_term}%"),
                Asset.application_name.ilike(f"%{search_term}%")
            )
        )
        
        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
        
        query = self._apply_context_filter(query)
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_infrastructure_data(
        self,
        asset_id: str,
        infrastructure_data: Dict[str, Any]
    ) -> bool:
        """Update asset infrastructure fields"""
        # Get asset to verify context
        asset = await self.get_by_id(asset_id)
        if not asset:
            return False
        
        # Map infrastructure fields that can be updated
        allowed_fields = {
            'cpu_cores', 'memory_gb', 'storage_gb', 'network_bandwidth_mbps',
            'operating_system', 'os_version', 'kernel_version',
            'virtualization_platform', 'container_platform',
            'cloud_provider', 'cloud_region', 'cloud_instance_type',
            'rack_location', 'data_center'
        }
        
        # Filter to only allowed fields
        update_data = {k: v for k, v in infrastructure_data.items() if k in allowed_fields}
        
        if update_data:
            update_data['updated_at'] = func.now()
            
            query = update(Asset).where(
                Asset.id == asset_id
            ).values(**update_data)
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
        
        return False
    
    async def update_business_data(
        self,
        asset_id: str,
        business_data: Dict[str, Any]
    ) -> bool:
        """Update asset business fields"""
        # Get asset to verify context
        asset = await self.get_by_id(asset_id)
        if not asset:
            return False
        
        # Map business fields that can be updated
        allowed_fields = {
            'business_unit', 'cost_center', 'owner_email',
            'technical_owner', 'business_owner',
            'compliance_requirements', 'business_criticality',
            'operational_hours', 'maintenance_window',
            'annual_cost', 'budget_code'
        }
        
        # Filter to only allowed fields
        update_data = {k: v for k, v in business_data.items() if k in allowed_fields}
        
        if update_data:
            update_data['updated_at'] = func.now()
            
            query = update(Asset).where(
                Asset.id == asset_id
            ).values(**update_data)
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
        
        return False
    
    async def update_migration_assessment(
        self,
        asset_id: str,
        assessment_data: Dict[str, Any]
    ) -> bool:
        """Update asset migration assessment data"""
        # Get asset to verify context
        asset = await self.get_by_id(asset_id)
        if not asset:
            return False
        
        # Map assessment fields
        allowed_fields = {
            'migration_readiness_score', 'recommended_migration_strategy',
            'migration_complexity', 'estimated_migration_effort_hours',
            'identified_risks', 'identified_blockers',
            'required_modifications', 'dependencies'
        }
        
        # Filter to only allowed fields
        update_data = {k: v for k, v in assessment_data.items() if k in allowed_fields}
        
        if update_data:
            update_data['updated_at'] = func.now()
            update_data['assessed_at'] = func.now()
            
            query = update(Asset).where(
                Asset.id == asset_id
            ).values(**update_data)
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
        
        return False
    
    async def bulk_create_from_discovery(
        self,
        discovery_flow_id: str,
        master_flow_id: str,
        assets_data: List[Dict[str, Any]]
    ) -> List[Asset]:
        """Create multiple assets from discovery data"""
        # Add flow IDs to all assets
        for asset_data in assets_data:
            asset_data['discovery_flow_id'] = discovery_flow_id
            asset_data['master_flow_id'] = master_flow_id
            asset_data['created_at'] = datetime.utcnow()
            asset_data['updated_at'] = datetime.utcnow()
        
        return await self.bulk_create(assets_data)
    
    async def get_asset_statistics(
        self,
        discovery_flow_id: Optional[str] = None,
        master_flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive asset statistics"""
        query = select(Asset)
        
        if discovery_flow_id:
            query = query.where(Asset.discovery_flow_id == discovery_flow_id)
        elif master_flow_id:
            query = query.where(Asset.master_flow_id == master_flow_id)
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        assets = result.scalars().all()
        
        # Calculate statistics
        total_assets = len(assets)
        
        # Group by type
        asset_types = {}
        for asset in assets:
            asset_type = asset.asset_type or 'unknown'
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        
        # Calculate readiness
        ready_for_migration = len([a for a in assets if a.migration_readiness_score and a.migration_readiness_score >= 70])
        needs_work = len([a for a in assets if a.migration_readiness_score and 40 <= a.migration_readiness_score < 70])
        not_ready = len([a for a in assets if a.migration_readiness_score and a.migration_readiness_score < 40])
        not_assessed = len([a for a in assets if not a.migration_readiness_score])
        
        # Group by migration strategy
        strategies = {}
        for asset in assets:
            strategy = asset.recommended_migration_strategy or 'not_assessed'
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        return {
            'total_assets': total_assets,
            'asset_types': asset_types,
            'migration_readiness': {
                'ready': ready_for_migration,
                'needs_work': needs_work,
                'not_ready': not_ready,
                'not_assessed': not_assessed
            },
            'migration_strategies': strategies,
            'average_readiness_score': (
                sum(a.migration_readiness_score for a in assets if a.migration_readiness_score) / 
                len([a for a in assets if a.migration_readiness_score])
                if any(a.migration_readiness_score for a in assets) else 0
            )
        }
    
    async def find_duplicate_assets(self) -> List[Dict[str, Any]]:
        """Find potential duplicate assets based on hostname or IP"""
        # This would need a more complex query to find duplicates
        # For now, return empty list
        return []
    
    async def mark_assets_for_wave(
        self,
        asset_ids: List[str],
        wave_number: int
    ) -> int:
        """Mark assets as assigned to a specific migration wave"""
        count = 0
        for asset_id in asset_ids:
            # Verify context for each asset
            asset = await self.get_by_id(asset_id)
            if asset:
                query = update(Asset).where(
                    Asset.id == asset_id
                ).values(
                    migration_wave_number=wave_number,
                    updated_at=func.now()
                )
                
                result = await self.db.execute(query)
                if result.rowcount > 0:
                    count += 1
        
        await self.db.commit()
        return count