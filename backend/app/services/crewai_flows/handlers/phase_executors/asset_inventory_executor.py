"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class AssetInventoryExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "inventory"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 50.0  # 3/6 phases
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for inventory crew
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        crew = self.crew_manager.create_crew_on_demand(
            "inventory", 
            cleaned_data=cleaned_data,
            field_mappings=field_mappings,
            **self._get_crew_context()
        )
        # Run crew in thread to avoid blocking async execution
        import asyncio
        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)
        
        # Process crew results
        results = self._process_crew_result(crew_result)
        
        # Persist assets to database after crew processing
        await self._persist_assets_to_database(results)
        
        return results
    
    async def execute_fallback(self) -> Dict[str, Any]:
        # 🚀 DATA VALIDATION: Check if we have data to process
        data_to_process = getattr(self.state, 'cleaned_data', None) or getattr(self.state, 'raw_data', [])
        if not data_to_process:
            return {"status": "skipped", "reason": "no_data", "total_assets": 0}
        
        # Simple fallback processing - create basic asset inventory from available data
        assets_count = len(data_to_process)
        
        # Basic asset classification based on asset type field
        servers = []
        applications = []
        devices = []
        
        for asset in data_to_process:
            asset_type = asset.get('Asset_Type', '').lower()
            if 'server' in asset_type:
                servers.append(asset)
            elif 'application' in asset_type or 'app' in asset_type:
                applications.append(asset)
            else:
                devices.append(asset)
        
        results = {
            "servers": servers,
            "applications": applications, 
            "devices": devices,
            "total_assets": assets_count,
            "classification_metadata": {
                "fallback_used": True,
                "servers_count": len(servers),
                "applications_count": len(applications),
                "devices_count": len(devices)
            }
        }
        
        # Persist assets to database even in fallback mode
        await self._persist_assets_to_database(results)
        
        return results
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        raw_data = getattr(self.state, 'raw_data', [])
        
        logger.info(f"🔍 Asset inventory crew input: {len(cleaned_data)} cleaned_data, {len(raw_data)} raw_data")
        
        return {"cleaned_data": cleaned_data}
    
    def _store_results(self, results: Dict[str, Any]):
        """Store results in state - persistence is handled in execute_with_crew"""
        self.state.asset_inventory = results
        
    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process asset inventory crew result and extract asset data"""
        logger.info(f"🔍 Processing asset inventory crew result: {type(crew_result)}")
        
        if hasattr(crew_result, 'raw') and crew_result.raw:
            logger.info(f"📄 Asset inventory crew raw output: {crew_result.raw[:200]}...")
            
            # Try to parse JSON from crew output
            import json
            try:
                if '{' in crew_result.raw and '}' in crew_result.raw:
                    start = crew_result.raw.find('{')
                    end = crew_result.raw.rfind('}') + 1
                    json_str = crew_result.raw[start:end]
                    parsed_result = json.loads(json_str)
                    
                    if any(key in parsed_result for key in ['servers', 'applications', 'devices', 'assets']):
                        logger.info("✅ Found structured asset data in crew output")
                        return parsed_result
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON from crew output: {e}")
            
            # Fallback: Use fallback processing
            logger.warning("⚠️ Asset inventory crew did not return structured data - using fallback")
            return self._execute_fallback_sync()
        
        elif isinstance(crew_result, dict):
            return crew_result
        
        else:
            logger.warning("⚠️ Unexpected crew result format - using fallback")
            return self._execute_fallback_sync()
    
    def _execute_fallback_sync(self) -> Dict[str, Any]:
        """Synchronous version of execute_fallback for crew result processing"""
        # Same logic as execute_fallback but synchronous
        data_to_process = getattr(self.state, 'cleaned_data', None) or getattr(self.state, 'raw_data', [])
        if not data_to_process:
            return {"status": "skipped", "reason": "no_data", "total_assets": 0}
        
        assets_count = len(data_to_process)
        
        # Basic asset classification
        servers = []
        applications = []
        devices = []
        
        for asset in data_to_process:
            asset_type = asset.get('Asset_Type', '').lower()
            if 'server' in asset_type:
                servers.append(asset)
            elif 'application' in asset_type or 'app' in asset_type:
                applications.append(asset)
            else:
                devices.append(asset)
        
        return {
            "servers": servers,
            "applications": applications, 
            "devices": devices,
            "total_assets": assets_count,
            "classification_metadata": {
                "fallback_used": True,
                "servers_count": len(servers),
                "applications_count": len(applications),
                "devices_count": len(devices)
            }
        }
    
    async def _persist_assets_to_database(self, results: Dict[str, Any]):
        """Persist discovered assets to the database"""
        try:
            logger.info("📦 Starting asset persistence to database")
            
            # Extract assets from results
            all_assets = []
            
            # Gather assets from different categories
            servers = results.get('servers', [])
            applications = results.get('applications', [])
            devices = results.get('devices', [])
            generic_assets = results.get('assets', [])
            
            # Combine all assets
            all_assets.extend(servers)
            all_assets.extend(applications)
            all_assets.extend(devices)
            all_assets.extend(generic_assets)
            
            if not all_assets:
                logger.warning("⚠️ No assets found to persist")
                return
            
            logger.info(f"📊 Found {len(all_assets)} assets to persist")
            
            # Get database session and context
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                # Get context from state
                context = None
                if hasattr(self.state, 'context'):
                    context = self.state.context
                elif hasattr(self.state, 'client_account_id') and hasattr(self.state, 'engagement_id'):
                    # Build context from state
                    from app.core.context import RequestContext
                    context = RequestContext(
                        client_account_id=self.state.client_account_id,
                        engagement_id=self.state.engagement_id,
                        user_id=getattr(self.state, 'user_id', None),
                        flow_id=getattr(self.state, 'flow_id', None)
                    )
                
                if not context:
                    logger.error("❌ No context available for asset persistence")
                    return
                
                logger.info(f"📋 Using context: client={context.client_account_id}, engagement={context.engagement_id}")
                
                # Get discovery flow ID
                discovery_flow_id = None
                if hasattr(self.state, 'discovery_flow_id'):
                    discovery_flow_id = self.state.discovery_flow_id
                elif hasattr(self.state, 'flow_internal_id'):
                    discovery_flow_id = self.state.flow_internal_id
                
                if not discovery_flow_id:
                    logger.error("❌ No discovery flow ID available for asset persistence")
                    return
                
                logger.info(f"🔗 Using discovery flow ID: {discovery_flow_id}")
                
                # Use AssetManager to persist assets
                from app.services.discovery_flow_service.managers.asset_manager import AssetManager
                asset_manager = AssetManager(db, context)
                
                # Prepare asset data for persistence
                asset_data_list = []
                for asset in all_assets:
                    # Transform raw asset data to the expected format
                    asset_data = {
                        'name': asset.get('Asset_Name') or asset.get('name') or 'Unknown Asset',
                        'asset_type': self._determine_asset_type(asset),
                        'hostname': asset.get('Hostname') or asset.get('hostname'),
                        'ip_address': asset.get('IP_Address') or asset.get('ip_address'),
                        'operating_system': asset.get('Operating_System') or asset.get('os'),
                        'environment': asset.get('Environment') or asset.get('environment') or 'production',
                        'criticality': asset.get('Criticality') or asset.get('criticality') or 'medium',
                        'status': 'discovered',
                        'application_name': asset.get('Application_Name') or asset.get('application_name'),
                        'cpu_cores': self._parse_int(asset.get('CPU_Cores') or asset.get('cpu_cores')),
                        'memory_gb': self._parse_float(asset.get('Memory_GB') or asset.get('memory_gb')),
                        'storage_gb': self._parse_float(asset.get('Storage_GB') or asset.get('storage_gb')),
                        'business_owner': asset.get('Business_Owner') or asset.get('business_owner'),
                        'technical_owner': asset.get('Technical_Owner') or asset.get('technical_owner'),
                        'department': asset.get('Department') or asset.get('department'),
                        'location': asset.get('Location') or asset.get('location'),
                        'datacenter': asset.get('Datacenter') or asset.get('datacenter'),
                        'raw_data': asset,  # Store original data
                        'field_mappings_used': getattr(self.state, 'field_mappings', {})
                    }
                    asset_data_list.append(asset_data)
                
                # Create assets in database
                created_assets = await asset_manager.create_assets_from_discovery(
                    discovery_flow_id=discovery_flow_id,
                    asset_data_list=asset_data_list,
                    discovered_in_phase='inventory'
                )
                
                logger.info(f"✅ Successfully persisted {len(created_assets)} assets to database")
                
                # Update state with created asset IDs
                if hasattr(self.state, 'created_asset_ids'):
                    self.state.created_asset_ids = [str(asset.id) for asset in created_assets]
                else:
                    self.state.created_asset_ids = [str(asset.id) for asset in created_assets]
                
        except Exception as e:
            logger.error(f"❌ Failed to persist assets to database: {e}", exc_info=True)
            # Don't raise - we don't want to fail the phase if persistence fails
    
    def _determine_asset_type(self, asset: Dict[str, Any]) -> str:
        """Determine asset type from asset data"""
        asset_type = asset.get('Asset_Type') or asset.get('asset_type') or ''
        asset_type = asset_type.lower()
        
        if 'server' in asset_type:
            return 'server'
        elif 'application' in asset_type or 'app' in asset_type:
            return 'application'
        elif 'database' in asset_type or 'db' in asset_type:
            return 'database'
        elif 'network' in asset_type:
            return 'network'
        elif 'storage' in asset_type:
            return 'storage'
        else:
            return 'other'
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Safely parse integer value"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Safely parse float value"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None