"""
V3 Asset Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.asset import V3AssetRepository
from app.models import Asset
from app.core.context import get_current_context
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class V3AssetService:
    """Service for V3 asset operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        self.db = db
        
        # Get context if not provided
        if not client_account_id or not engagement_id:
            try:
                context = get_current_context()
                client_account_id = client_account_id or str(context.client_account_id)
                engagement_id = engagement_id or str(context.engagement_id)
            except:
                # Default fallback if context not available
                client_account_id = client_account_id or str(uuid.uuid4())
                engagement_id = engagement_id or str(uuid.uuid4())
        
        self.asset_repo = V3AssetRepository(db, client_account_id, engagement_id)
    
    async def create_assets_from_discovery(
        self,
        discovery_flow_id: str,
        master_flow_id: str,
        discovered_assets: List[Dict[str, Any]]
    ) -> List[Asset]:
        """Create assets from discovery data"""
        try:
            # Prepare asset data with proper field names
            assets_data = []
            for asset_data in discovered_assets:
                # Handle field renames if needed
                prepared_asset = self._prepare_asset_data(asset_data)
                assets_data.append(prepared_asset)
            
            # Bulk create assets
            assets = await self.asset_repo.bulk_create_from_discovery(
                discovery_flow_id,
                master_flow_id,
                assets_data
            )
            
            logger.info(f"Created {len(assets)} assets for flow {discovery_flow_id}")
            
            return assets
            
        except Exception as e:
            logger.error(f"Failed to create assets from discovery: {e}")
            raise
    
    def _prepare_asset_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare asset data with proper field names and types"""
        # Start with a copy of raw data
        asset_data = raw_data.copy()
        
        # Ensure required fields
        if 'asset_name' not in asset_data and 'hostname' in asset_data:
            asset_data['asset_name'] = asset_data['hostname']
        
        # Set asset type if not provided
        if 'asset_type' not in asset_data:
            # Try to infer asset type
            if 'database' in str(asset_data.get('asset_name', '')).lower():
                asset_data['asset_type'] = 'database'
            elif 'app' in str(asset_data.get('asset_name', '')).lower():
                asset_data['asset_type'] = 'application'
            else:
                asset_data['asset_type'] = 'server'
        
        # Handle numeric conversions
        numeric_fields = [
            'cpu_cores', 'memory_gb', 'storage_gb', 
            'network_bandwidth_mbps', 'annual_cost',
            'migration_readiness_score', 'estimated_migration_effort_hours'
        ]
        
        for field in numeric_fields:
            if field in asset_data and asset_data[field] is not None:
                try:
                    if field.endswith('_gb') or field == 'annual_cost':
                        asset_data[field] = float(asset_data[field])
                    else:
                        asset_data[field] = int(asset_data[field])
                except (ValueError, TypeError):
                    asset_data[field] = None
        
        # Set timestamps
        now = datetime.utcnow()
        asset_data['discovered_at'] = asset_data.get('discovered_at', now)
        asset_data['last_seen_at'] = asset_data.get('last_seen_at', now)
        
        return asset_data
    
    async def get_assets_by_flow(
        self,
        discovery_flow_id: Optional[str] = None,
        master_flow_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get assets by discovery or master flow"""
        if discovery_flow_id:
            assets = await self.asset_repo.get_by_discovery_flow(discovery_flow_id)
        elif master_flow_id:
            assets = await self.asset_repo.get_by_master_flow(master_flow_id)
        else:
            assets = await self.asset_repo.list_all(limit=100)
        
        return [self._serialize_asset(asset) for asset in assets]
    
    async def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific asset by ID"""
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset:
            return None
        
        return self._serialize_asset(asset)
    
    async def search_assets(
        self,
        search_term: str,
        asset_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search assets by various criteria"""
        assets = await self.asset_repo.search_assets(search_term, asset_type, limit)
        return [self._serialize_asset(asset) for asset in assets]
    
    async def update_asset_infrastructure(
        self,
        asset_id: str,
        infrastructure_data: Dict[str, Any]
    ) -> bool:
        """Update asset infrastructure information"""
        try:
            success = await self.asset_repo.update_infrastructure_data(
                asset_id,
                infrastructure_data
            )
            
            if success:
                logger.info(f"Updated infrastructure data for asset {asset_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update infrastructure data: {e}")
            return False
    
    async def update_asset_business_info(
        self,
        asset_id: str,
        business_data: Dict[str, Any]
    ) -> bool:
        """Update asset business information"""
        try:
            success = await self.asset_repo.update_business_data(
                asset_id,
                business_data
            )
            
            if success:
                logger.info(f"Updated business data for asset {asset_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update business data: {e}")
            return False
    
    async def assess_asset_migration(
        self,
        asset_id: str,
        assessment_data: Dict[str, Any]
    ) -> bool:
        """Update asset migration assessment"""
        try:
            success = await self.asset_repo.update_migration_assessment(
                asset_id,
                assessment_data
            )
            
            if success:
                logger.info(f"Updated migration assessment for asset {asset_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update migration assessment: {e}")
            return False
    
    async def get_asset_statistics(
        self,
        discovery_flow_id: Optional[str] = None,
        master_flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive asset statistics"""
        return await self.asset_repo.get_asset_statistics(
            discovery_flow_id,
            master_flow_id
        )
    
    async def assign_assets_to_wave(
        self,
        asset_ids: List[str],
        wave_number: int
    ) -> Dict[str, Any]:
        """Assign multiple assets to a migration wave"""
        try:
            assigned_count = await self.asset_repo.mark_assets_for_wave(
                asset_ids,
                wave_number
            )
            
            logger.info(f"Assigned {assigned_count} assets to wave {wave_number}")
            
            return {
                "requested": len(asset_ids),
                "assigned": assigned_count,
                "wave_number": wave_number
            }
            
        except Exception as e:
            logger.error(f"Failed to assign assets to wave: {e}")
            raise
    
    async def find_duplicate_assets(self) -> List[Dict[str, Any]]:
        """Find potential duplicate assets"""
        duplicates = await self.asset_repo.find_duplicate_assets()
        
        return [
            {
                "group": dup.get("group"),
                "assets": [self._serialize_asset(asset) for asset in dup.get("assets", [])]
            }
            for dup in duplicates
        ]
    
    def _serialize_asset(self, asset: Asset) -> Dict[str, Any]:
        """Serialize asset for API response"""
        return {
            "id": str(asset.id),
            "master_flow_id": str(asset.master_flow_id) if asset.master_flow_id else None,
            "discovery_flow_id": str(asset.discovery_flow_id) if asset.discovery_flow_id else None,
            
            # Basic info
            "asset_name": asset.asset_name,
            "asset_type": asset.asset_type,
            "hostname": asset.hostname,
            "ip_address": asset.ip_address,
            
            # Infrastructure details
            "cpu_cores": asset.cpu_cores,
            "memory_gb": asset.memory_gb,
            "storage_gb": asset.storage_gb,
            "operating_system": asset.operating_system,
            "os_version": asset.os_version,
            "environment": asset.environment,
            "location": asset.location,
            
            # Business info
            "business_unit": asset.business_unit,
            "business_criticality": asset.business_criticality,
            "owner_email": asset.owner_email,
            "technical_owner": asset.technical_owner,
            "business_owner": asset.business_owner,
            
            # Migration assessment
            "migration_readiness_score": asset.migration_readiness_score,
            "recommended_migration_strategy": asset.recommended_migration_strategy,
            "migration_complexity": asset.migration_complexity,
            "migration_wave_number": asset.migration_wave_number,
            "estimated_migration_effort_hours": asset.estimated_migration_effort_hours,
            
            # Status and timestamps
            "status": asset.status,
            "discovered_at": asset.discovered_at.isoformat() if asset.discovered_at else None,
            "last_seen_at": asset.last_seen_at.isoformat() if asset.last_seen_at else None,
            "assessed_at": asset.assessed_at.isoformat() if asset.assessed_at else None,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
        }
    
    async def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset"""
        try:
            success = await self.asset_repo.delete(asset_id)
            
            if success:
                logger.info(f"Deleted asset {asset_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete asset: {e}")
            return False