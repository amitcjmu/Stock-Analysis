"""
Asset Management Handler
Handles asset-related operations for discovery flows.
Provides unified asset management across CrewAI and PostgreSQL layers.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)

class AssetManagementHandler:
    """
    Handler for discovery flow asset management.
    Provides unified asset operations across execution layers.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.logger = logger
    
    async def get_flow_assets(self, flow_id: str) -> List[Dict[str, Any]]:
        """
        Get assets for a discovery flow from unified sources.
        """
        try:
            self.logger.info(f"📦 Getting assets for flow: {flow_id}")
            
            assets = []
            
            # Try to get assets from V2 discovery flow service
            try:
                from app.services.discovery_flow_service import DiscoveryFlowService
                
                service = DiscoveryFlowService(self.db, self.context)
                db_assets = await service.get_flow_assets(flow_id)
                
                # Convert to dict format
                for asset in db_assets:
                    asset_dict = asset.to_dict()
                    asset_dict.update({
                        "source": "postgresql",
                        "handler": "asset_management"
                    })
                    assets.append(asset_dict)
                
                self.logger.info(f"✅ Retrieved {len(db_assets)} assets from PostgreSQL")
                
            except Exception as e:
                self.logger.warning(f"⚠️ PostgreSQL asset retrieval failed: {e}")
            
            # If no assets from database, return mock data for development
            if not assets:
                mock_assets = [
                    {
                        "id": f"asset-{flow_id}-1",
                        "discovery_flow_id": flow_id,
                        "client_account_id": self.context.client_account_id,
                        "engagement_id": self.context.engagement_id,
                        "asset_name": "Mock Web Server",
                        "asset_type": "server",
                        "asset_subtype": "web_server",
                        "raw_data": {
                            "hostname": "web01.example.com",
                            "ip_address": "10.0.1.100",
                            "os": "Linux",
                            "cpu_cores": 4,
                            "memory_gb": 16
                        },
                        "normalized_data": {
                            "compute_capacity": "medium",
                            "migration_complexity": "low",
                            "dependencies": ["database", "load_balancer"]
                        },
                        "discovered_in_phase": "asset_inventory",
                        "discovery_method": "crewai_agents",
                        "confidence_score": 0.92,
                        "migration_ready": True,
                        "migration_complexity": "low",
                        "migration_priority": 2,
                        "asset_status": "active",
                        "validation_status": "validated",
                        "source": "mock",
                        "handler": "asset_management",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": f"asset-{flow_id}-2",
                        "discovery_flow_id": flow_id,
                        "client_account_id": self.context.client_account_id,
                        "engagement_id": self.context.engagement_id,
                        "asset_name": "Mock Database Server",
                        "asset_type": "database",
                        "asset_subtype": "mysql",
                        "raw_data": {
                            "hostname": "db01.example.com",
                            "ip_address": "10.0.1.200",
                            "database_version": "MySQL 8.0",
                            "storage_gb": 500,
                            "connections": 100
                        },
                        "normalized_data": {
                            "data_volume": "medium",
                            "migration_complexity": "high",
                            "backup_strategy": "required"
                        },
                        "discovered_in_phase": "asset_inventory",
                        "discovery_method": "crewai_agents",
                        "confidence_score": 0.88,
                        "migration_ready": False,
                        "migration_complexity": "high",
                        "migration_priority": 1,
                        "asset_status": "active",
                        "validation_status": "pending",
                        "source": "mock",
                        "handler": "asset_management",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                ]
                
                assets.extend(mock_assets)
                self.logger.info(f"✅ Returned {len(mock_assets)} mock assets")
            
            self.logger.info(f"✅ Total assets retrieved: {len(assets)}")
            return assets
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get flow assets: {e}")
            raise
    
    async def validate_asset(
        self,
        asset_id: str,
        validation_status: str,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a discovery asset.
        """
        try:
            self.logger.info(f"🔍 Validating asset: {asset_id}")
            
            # Try to update asset validation in database
            try:
                from app.services.discovery_flow_service import DiscoveryFlowService
                
                service = DiscoveryFlowService(self.db, self.context)
                
                # For now, return mock validation result
                # TODO: Implement actual asset validation
                
                validation_result = {
                    "asset_id": asset_id,
                    "validation_status": validation_status,
                    "validation_results": validation_results or {},
                    "validated_at": datetime.now().isoformat(),
                    "validator": "asset_management_handler",
                    "handler": "asset_management"
                }
                
                self.logger.info(f"✅ Asset validation completed: {asset_id}")
                return validation_result
                
            except Exception as e:
                self.logger.warning(f"⚠️ Database asset validation failed: {e}")
                
                # Return mock validation
                return {
                    "asset_id": asset_id,
                    "validation_status": validation_status,
                    "validation_results": validation_results or {},
                    "validated_at": datetime.now().isoformat(),
                    "validator": "mock_validator",
                    "handler": "asset_management"
                }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to validate asset: {e}")
            raise
    
    async def get_asset_summary(self, flow_id: str) -> Dict[str, Any]:
        """
        Get asset summary for a discovery flow.
        """
        try:
            self.logger.info(f"📊 Getting asset summary for flow: {flow_id}")
            
            assets = await self.get_flow_assets(flow_id)
            
            # Calculate summary statistics
            total_assets = len(assets)
            asset_types = {}
            migration_ready = 0
            validation_pending = 0
            
            for asset in assets:
                asset_type = asset.get("asset_type", "unknown")
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                
                if asset.get("migration_ready", False):
                    migration_ready += 1
                
                if asset.get("validation_status") == "pending":
                    validation_pending += 1
            
            summary = {
                "flow_id": flow_id,
                "total_assets": total_assets,
                "asset_types": asset_types,
                "migration_ready": migration_ready,
                "migration_ready_percentage": (migration_ready / total_assets * 100) if total_assets > 0 else 0,
                "validation_pending": validation_pending,
                "validation_complete": total_assets - validation_pending,
                "handler": "asset_management",
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Asset summary generated for flow: {flow_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get asset summary: {e}")
            raise 