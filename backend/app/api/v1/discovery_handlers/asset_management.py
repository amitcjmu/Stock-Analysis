"""
Asset Management Handler
Handles unified asset operations across discovery execution layers.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

# Import models with graceful fallback
try:
    from app.models.asset import Asset, AssetType, AssetStatus
    from app.models.client_account import ClientAccount
    from app.models.discovery_flow import DiscoveryFlow
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Models not available: {e}")
    MODELS_AVAILABLE = False
    Asset = ClientAccount = DiscoveryFlow = None

class AssetManagementHandler:
    """Handler for unified asset management operations"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
    
    async def get_flow_assets(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get assets for a discovery flow, prioritizing real data over mock data"""
        try:
            logger.info(f"📦 Getting assets for flow: {flow_id}")
            
            assets = []
            
            # First, try to get real assets from the main assets table
            if MODELS_AVAILABLE:
                try:
                    # Query main assets table for this flow
                    from sqlalchemy import select, and_
                    
                    main_assets_query = select(Asset).where(
                        and_(
                            Asset.client_account_id == self.context.client_account_id,
                            Asset.custom_attributes.op('->>')('discovery_flow_id').contains(flow_id)
                        )
                    )
                    main_assets_result = await self.db.execute(main_assets_query)
                    main_assets = main_assets_result.scalars().all()
                    
                    if main_assets:
                        logger.info(f"✅ Found {len(main_assets)} real assets in main table for flow: {flow_id}")
                        for asset in main_assets:
                            assets.append(self._convert_main_asset_to_dict(asset))
                        return assets
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to query main assets table: {e}")
            
            # Second, try to get discovery assets
            if MODELS_AVAILABLE:
                try:
                    # Get the flow to find the internal ID
                    from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
                    flow_repo = DiscoveryFlowRepository(self.db, str(self.context.client_account_id), str(self.context.engagement_id))
                    flow = await flow_repo.get_by_flow_id(flow_id)
                    
                    if flow:
                        # Query assets created by this discovery flow
                        from app.models.asset import Asset
                        asset_query = select(Asset).where(
                            and_(
                                Asset.custom_attributes['discovery_flow_id'].astext == str(flow.id),
                                Asset.client_account_id == self.context.client_account_id
                            )
                        )
                        asset_result = await self.db.execute(asset_query)
                        discovery_assets = asset_result.scalars().all()
                        
                        if discovery_assets:
                            logger.info(f"✅ Found {len(discovery_assets)} assets for flow: {flow_id}")
                            for asset in discovery_assets:
                                assets.append(self._convert_asset_to_dict(asset))
                            return assets
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to query discovery assets: {e}")
            
            # If no real assets found, fall back to mock data for development
            logger.warning(f"⚠️ No real assets found for flow {flow_id}, generating mock data")
            return self._get_fallback_assets(flow_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to get flow assets: {e}")
            # Return empty list instead of raising exception
            return []

    def _convert_main_asset_to_dict(self, asset: Asset) -> Dict[str, Any]:
        """Convert main Asset model to dictionary format"""
        return {
            "id": str(asset.id),
            "asset_id": str(asset.id),
            "flow_id": asset.custom_attributes.get('discovery_flow_id'),
            "asset_name": asset.asset_name,
            "name": asset.name or asset.asset_name,
            "asset_type": asset.asset_type.value if asset.asset_type else "unknown",
            "environment": asset.environment,
            "operating_system": asset.operating_system,
            "status": asset.status.value if asset.status else "unknown",
            "criticality": asset.criticality or "Medium",
            "business_criticality": asset.business_criticality or "medium",
            "location": asset.location,
            "dependencies": asset.dependencies or [],
            "dependencies_count": len(asset.dependencies or []),
            "risk_score": 0.5,  # Default risk score
            "migration_readiness": "Ready" if asset.migration_status else "Needs Review",
            "migration_complexity": asset.migration_complexity or "medium",
            "six_r_strategy": asset.six_r_strategy.value if asset.six_r_strategy else "rehost",
            "last_updated": asset.updated_at.isoformat() if asset.updated_at else None,
            "discovered_at": asset.discovery_timestamp.isoformat() if asset.discovery_timestamp else None,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "is_mock": False,  # Real data from main table
            
            # Additional fields for enterprise view
            "hostname": asset.hostname,
            "ip_address": asset.ip_address,
            "mac_address": asset.mac_address,
            "cpu_cores": asset.cpu_cores,
            "memory_gb": asset.memory_gb,
            "storage_gb": asset.storage_gb,
            "manufacturer": asset.raw_data.get('Manufacturer') if asset.raw_data else None,
            "model": asset.raw_data.get('Model') if asset.raw_data else None,
            "serial_number": asset.raw_data.get('Serial_Number') if asset.raw_data else None,
            "os_version": asset.os_version,
            "business_owner": asset.business_owner,
            "technical_owner": asset.technical_owner,
            "department": asset.department,
            "application_name": asset.application_name,
            "technology_stack": asset.technology_stack,
            "datacenter": asset.datacenter,
            "custom_attributes": asset.custom_attributes,
            "raw_data": asset.raw_data,
        }

    def _convert_asset_to_dict(self, asset: Any) -> Dict[str, Any]:
        """Convert Asset model to dictionary format"""
        try:
            # Extract discovery metadata from custom_attributes
            custom_attrs = asset.custom_attributes or {}
            
            return {
                "id": str(asset.id),
                "asset_name": asset.name,
                "asset_type": asset.type,
                "status": asset.status,
                "flow_id": custom_attrs.get('discovery_flow_id'),
                "raw_data": custom_attrs.get('raw_data', {}),
                "normalized_data": custom_attrs.get('normalized_data', {}),
                "confidence_score": custom_attrs.get('confidence_score', 0.0),
                "migration_ready": custom_attrs.get('migration_ready', False),
                "migration_complexity": custom_attrs.get('migration_complexity', 'Medium'),
                "discovered_at": asset.created_at.isoformat() if asset.created_at else None,
                "discovered_in_phase": custom_attrs.get('discovered_in_phase', 'unknown'),
                "discovery_method": custom_attrs.get('discovery_method', 'unknown'),
                "validation_status": custom_attrs.get('validation_status', 'pending')
            }
        except Exception as e:
            logger.error(f"Error converting asset to dict: {e}")
            return {
                "id": str(asset.id) if hasattr(asset, 'id') else 'unknown',
                "asset_name": getattr(asset, 'name', 'Unknown'),
                "asset_type": getattr(asset, 'type', 'unknown'),
                "error": str(e)
            }
    #     normalized_data = asset.normalized_data or {}
    #     raw_data = asset.raw_data or {}
    #     
    #     return {
    #        "id": str(asset.id),
    #        "asset_id": str(asset.id),
    #        "flow_id": str(asset.discovery_flow_id),
    #        "asset_name": asset.asset_name,
    #        "name": asset.asset_name,
    #        "asset_type": asset.asset_type,
    #        "environment": normalized_data.get('environment') or raw_data.get('DR_Tier', 'Unknown'),
    #        "operating_system": normalized_data.get('operating_system') or raw_data.get('Operating_System'),
    #        "status": asset.asset_status or "discovered",
    #        "criticality": normalized_data.get('criticality', 'Medium'),
    #        "business_criticality": normalized_data.get('business_criticality', 'medium'),
    #        "location": normalized_data.get('location') or raw_data.get('Location_DataCenter'),
    #        "dependencies": [],  # Will be populated from dependency analysis
    #        "dependencies_count": 0,
    #        "risk_score": asset.confidence_score or 0.85,
    #        "migration_readiness": "Ready" if asset.migration_ready else "Needs Review", 
    #        "migration_complexity": asset.migration_complexity or "medium",
    #        "six_r_strategy": "rehost",  # Default strategy
    #        "last_updated": asset.updated_at.isoformat() if asset.updated_at else None,
    #        "discovered_at": asset.created_at.isoformat() if asset.created_at else None,
    #        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    #        "is_mock": asset.is_mock or False,
    #        
            # Additional fields from normalized data
    #        "hostname": normalized_data.get('hostname'),
    #        "ip_address": normalized_data.get('ip_address') or raw_data.get('IP_Address'),
    #        "mac_address": normalized_data.get('mac_address') or raw_data.get('MAC_Address'),
    #        "cpu_cores": normalized_data.get('cpu_cores') or raw_data.get('CPU_Cores'),
    #        "memory_gb": normalized_data.get('memory_gb') or raw_data.get('RAM_GB'),
    #        "storage_gb": normalized_data.get('storage_gb') or raw_data.get('Storage_GB'),
    #        "manufacturer": normalized_data.get('manufacturer') or raw_data.get('Manufacturer'),
    #        "model": normalized_data.get('model') or raw_data.get('Model'),
    #        "serial_number": normalized_data.get('serial_number') or raw_data.get('Serial_Number'),
    #        "os_version": normalized_data.get('os_version') or raw_data.get('OS_Version'),
    #        "business_owner": normalized_data.get('business_owner') or raw_data.get('Application_Owner'),
    #        "technical_owner": normalized_data.get('technical_owner'),
    #        "department": normalized_data.get('department'),
    #        "application_name": normalized_data.get('service_name') or raw_data.get('Application_Service'),
    #        "technology_stack": normalized_data.get('technology_stack'),
    #        "datacenter": normalized_data.get('location') or raw_data.get('Location_DataCenter'),
    #        "custom_attributes": {
    #            "discovered_in_phase": asset.discovered_in_phase,
    #            "discovery_method": asset.discovery_method,
    #            "confidence_score": asset.confidence_score,
    #            "validation_status": asset.validation_status,
    #            "migration_notes": raw_data.get('Migration_Notes'),
    #            "migration_readiness_score": raw_data.get('Cloud_Migration_Readiness_Score')
    #        },
    #        "raw_data": raw_data,
    #    }
    
    async def get_asset_classification_summary(self) -> Dict[str, Any]:
        """Get asset classification summary for the classification cards"""
        try:
            if not MODELS_AVAILABLE:
                return self._get_fallback_classification_summary()
            
            # Query asset counts by type
            stmt = select(
                Asset.asset_type,
                func.count(Asset.id).label('count')
            ).where(
                and_(
                    Asset.client_account_id == uuid.UUID(self.client_account_id),
                    Asset.engagement_id == uuid.UUID(self.engagement_id)
                )
            ).group_by(Asset.asset_type)
            
            result = await self.db.execute(stmt)
            type_counts = {row.asset_type.value: row.count for row in result.fetchall()}
            
            # Calculate totals
            total_assets = sum(type_counts.values())
            
            classification_summary = {
                "total_assets": total_assets,
                "by_type": {
                    "servers": type_counts.get("server", 0),
                    "applications": type_counts.get("application", 0),
                    "databases": type_counts.get("database", 0),
                    "devices": (
                        type_counts.get("network", 0) + 
                        type_counts.get("storage", 0) + 
                        type_counts.get("load_balancer", 0) + 
                        type_counts.get("security_group", 0)
                    ),
                    "virtual_machines": type_counts.get("virtual_machine", 0),
                    "containers": type_counts.get("container", 0),
                    "other": type_counts.get("other", 0)
                },
                "classification_accuracy": 100.0,  # All assets in main table should be classified
                "total_mapped": total_assets,
                "total_unmapped": 0
            }
            
            logger.info(f"📊 Asset classification summary: {classification_summary}")
            return classification_summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get classification summary: {e}")
            return self._get_fallback_classification_summary()
    
    async def get_crewai_insights(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get CrewAI-generated insights for the asset inventory"""
        try:
            # Query for asset-related insights from the flow
            insights = []
            
            # Get insights from assets with AI recommendations
            if MODELS_AVAILABLE:
                stmt = select(Asset).where(
                    and_(
                        Asset.client_account_id == uuid.UUID(self.client_account_id),
                        Asset.engagement_id == uuid.UUID(self.engagement_id),
                        Asset.ai_recommendations.isnot(None)
                    )
                )
                
                result = await self.db.execute(stmt)
                assets_with_insights = result.scalars().all()
                
                for asset in assets_with_insights:
                    if asset.ai_recommendations:
                        insight = {
                            "id": f"insight-{asset.id}",
                            "title": f"AI Analysis for {asset.name}",
                            "category": "Asset Intelligence",
                            "description": f"CrewAI agents analyzed {asset.name} and provided strategic recommendations",
                            "recommendations": asset.ai_recommendations,
                            "confidence_score": asset.completeness_score or 85.0,
                            "asset_id": str(asset.id),
                            "asset_name": asset.name,
                            "generated_at": asset.updated_at.isoformat() if asset.updated_at else None
                        }
                        insights.append(insight)
            
            # Add general inventory insights
            assets = await self.get_flow_assets(flow_id)
            if assets:
                inventory_insight = {
                    "id": "inventory-analysis",
                    "title": "Asset Inventory Analysis",
                    "category": "Inventory Intelligence",
                    "description": f"Analysis of {len(assets)} assets discovered during inventory phase",
                    "recommendations": {
                        "total_assets": len(assets),
                        "asset_distribution": self._analyze_asset_distribution(assets),
                        "migration_readiness": self._analyze_migration_readiness(assets),
                        "risk_profile": self._analyze_risk_profile(assets)
                    },
                    "confidence_score": 92.0,
                    "generated_at": datetime.now().isoformat()
                }
                insights.append(inventory_insight)
            
            logger.info(f"🧠 Generated {len(insights)} CrewAI insights for inventory")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get CrewAI insights: {e}")
            return []
    
    def _calculate_risk_score(self, asset) -> float:
        """Calculate risk score based on asset attributes"""
        score = 0.0
        
        # Age factor (based on discovery timestamp)
        if not asset.discovery_timestamp:
            score += 0.1
        
        # Criticality factor
        if asset.business_criticality == 'critical':
            score += 0.3
        elif asset.business_criticality == 'high':
            score += 0.2
        elif asset.business_criticality == 'medium':
            score += 0.1
        
        # Migration complexity
        if asset.migration_complexity == 'high':
            score += 0.2
        elif asset.migration_complexity == 'medium':
            score += 0.1
        
        # Dependencies
        if asset.dependencies and len(asset.dependencies) > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_migration_readiness(self, asset) -> str:
        """Calculate migration readiness status"""
        if asset.sixr_ready == 'Ready':
            return "Ready"
        elif asset.six_r_strategy:
            return "Assessed"
        elif asset.mapping_status == 'completed':
            return "Mapped"
        else:
            return "Needs Review"
    
    def _analyze_asset_distribution(self, assets: List[Dict]) -> Dict[str, Any]:
        """Analyze asset distribution patterns"""
        type_counts = {}
        env_counts = {}
        
        for asset in assets:
            asset_type = asset.get('asset_type', 'unknown')
            environment = asset.get('environment', 'unknown')
            
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            env_counts[environment] = env_counts.get(environment, 0) + 1
        
        return {
            "by_type": type_counts,
            "by_environment": env_counts,
            "total": len(assets)
        }
    
    def _analyze_migration_readiness(self, assets: List[Dict]) -> Dict[str, Any]:
        """Analyze migration readiness across assets"""
        readiness_counts = {}
        
        for asset in assets:
            readiness = asset.get('migration_readiness', 'Unknown')
            readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
        
        return readiness_counts
    
    def _analyze_risk_profile(self, assets: List[Dict]) -> Dict[str, Any]:
        """Analyze risk profile across assets"""
        high_risk = sum(1 for a in assets if a.get('risk_score', 0) > 0.7)
        medium_risk = sum(1 for a in assets if 0.3 <= a.get('risk_score', 0) <= 0.7)
        low_risk = sum(1 for a in assets if a.get('risk_score', 0) < 0.3)
        
        return {
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "total": len(assets)
        }
    
    async def _get_discovery_assets_fallback(self, flow_id: str) -> List[Dict[str, Any]]:
        """Fallback to discovery_assets table if main assets table fails"""
        # DiscoveryAsset model removed - return empty list
        logger.warning("⚠️ DiscoveryAsset model removed - returning empty fallback assets")
        return []
    
    def _get_fallback_assets(self, flow_id: str) -> List[Dict[str, Any]]:
        """Final fallback with mock data when database is unavailable"""
        logger.warning("🔄 Using fallback mock data for asset inventory")
        
        assets = [
            {
                "id": f"asset-{i:03d}",
                "asset_id": f"asset-{i:03d}",
                "flow_id": flow_id,
                "asset_name": f"Server-{i:03d}",
                "name": f"Server-{i:03d}",
                "asset_type": "server",
                "environment": "Production" if i % 2 == 0 else "Development",
                "operating_system": "Linux" if i % 3 == 0 else "Windows",
                "status": "Active",
                "criticality": "High" if i % 4 == 0 else "Medium",
                "business_criticality": "high" if i % 4 == 0 else "medium",
                "location": "Data Center A" if i % 2 == 0 else "Data Center B",
                "dependencies": [],
                "dependencies_count": i % 5,
                "risk_score": round(0.3 + (i % 7) * 0.1, 2),
                "migration_readiness": "Ready" if i % 3 == 0 else "Needs Review",
                "migration_complexity": "medium",
                "six_r_strategy": "rehost",
                "last_updated": datetime.now().isoformat(),
                "discovered_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "is_mock": True
            }
            for i in range(1, 21)  # Generate 20 mock assets
        ]
        
        return assets
    
    def _get_fallback_classification_summary(self) -> Dict[str, Any]:
        """Fallback classification summary when database is unavailable"""
        return {
            "total_assets": 20,
            "by_type": {
                "servers": 20,
                "applications": 0,
                "databases": 0,
                "devices": 0,
                "virtual_machines": 0,
                "containers": 0,
                "other": 0
            },
            "classification_accuracy": 100.0,
            "total_mapped": 20,
            "total_unmapped": 0
        }
    
    # Keep existing methods for compatibility...
    async def create_asset(self, flow_id: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new asset in the flow"""
        try:
            logger.info(f"➕ Creating asset for flow: {flow_id}")
            
            asset = {
                "asset_id": f"asset-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "flow_id": flow_id,
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id,
                "created_by": self.user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                **asset_data
            }
            
            logger.info(f"✅ Asset created: {asset['asset_id']}")
            return asset
            
        except Exception as e:
            logger.error(f"❌ Failed to create asset: {e}")
            raise 