"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class AssetInventoryExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "inventory"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 50.0  # 3/6 phases
    
    def _get_phase_timeout(self) -> int:
        """Asset inventory needs more time for processing"""
        return 120  # 2 minutes for asset processing
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for inventory crew
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        logger.info(f"🚀 Starting asset inventory crew execution with {len(cleaned_data)} records")
        
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
        # NO FALLBACK LOGIC - FAIL FAST TO IDENTIFY REAL ISSUES
        logger.error("❌ FALLBACK EXECUTION DISABLED - Asset inventory crew must work properly")
        logger.error("❌ If you see this error, fix the actual crew execution issues")
        raise RuntimeError("Asset inventory fallback disabled - crew execution failed")
    
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
        """Process asset inventory crew result and extract asset data - NO FALLBACKS"""
        logger.info(f"🔍 Processing asset inventory crew result: {type(crew_result)}")
        
        if hasattr(crew_result, 'raw') and crew_result.raw:
            logger.info(f"📄 Asset inventory crew raw output: {crew_result.raw}")
            
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
                    else:
                        logger.error(f"❌ Crew returned JSON but missing required keys. Got: {list(parsed_result.keys())}")
                        raise ValueError("Asset inventory crew returned JSON without required asset categories")
                else:
                    logger.error(f"❌ Crew output does not contain valid JSON structure: {crew_result.raw}")
                    raise ValueError("Asset inventory crew did not return JSON output")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Failed to parse JSON from crew output: {e}")
                logger.error(f"❌ Raw crew output: {crew_result.raw}")
                raise RuntimeError(f"Asset inventory crew output parsing failed: {e}")
        
        elif isinstance(crew_result, dict):
            # Validate that required keys exist
            if any(key in crew_result for key in ['servers', 'applications', 'devices', 'assets']):
                logger.info("✅ Crew returned valid dict with asset data")
                return crew_result
            else:
                logger.error(f"❌ Crew returned dict but missing required asset keys. Got: {list(crew_result.keys())}")
                raise ValueError("Asset inventory crew returned dict without required asset categories")
        
        else:
            logger.error(f"❌ Unexpected crew result format: {type(crew_result)}")
            logger.error(f"❌ Crew result: {crew_result}")
            raise RuntimeError(f"Asset inventory crew returned unexpected result type: {type(crew_result)}")
    
    def _execute_fallback_sync(self) -> Dict[str, Any]:
        """NO SYNC FALLBACK - This method should never be called"""
        logger.error("❌ _execute_fallback_sync called - this method is disabled")
        raise RuntimeError("Sync fallback disabled - crew execution must work properly")
    
    async def _persist_assets_to_database(self, results: Dict[str, Any]):
        """Persist discovered assets to the database with deduplication"""
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
            
            # Note: Deduplication is handled by intelligent agents using deduplication tools
            # The inventory manager has instructions to avoid creating duplicates
            
            # Debug: Log state attributes
            logger.info(f"🔍 State attributes: {[attr for attr in dir(self.state) if not attr.startswith('_')]}")
            logger.info(f"🔍 State has flow_id: {hasattr(self.state, 'flow_id')}")
            logger.info(f"🔍 State has client_account_id: {hasattr(self.state, 'client_account_id')}")
            logger.info(f"🔍 State has engagement_id: {hasattr(self.state, 'engagement_id')}")
            
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
                else:
                    # Try to get context from flow_bridge if available
                    if self.flow_bridge and hasattr(self.flow_bridge, 'context'):
                        context = self.flow_bridge.context
                        logger.info(f"🔄 Using context from flow_bridge: client={context.client_account_id}, engagement={context.engagement_id}")
                
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
                elif hasattr(self.state, 'flow_id'):
                    discovery_flow_id = self.state.flow_id
                
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
                        'type': self._determine_asset_type(asset),  # CC FIX: Use 'type' not 'asset_type' for AssetCommands
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
                        'field_mappings_used': getattr(self.state, 'field_mappings', {}),
                        'normalized_data': {  # CC FIX: Add normalized_data structure for better field mapping
                            'hostname': asset.get('Hostname') or asset.get('hostname'),
                            'operating_system': asset.get('Operating_System') or asset.get('os'),
                            'environment': asset.get('Environment') or asset.get('environment') or 'production',
                            'criticality': asset.get('Criticality') or asset.get('criticality') or 'medium',
                            'application_name': asset.get('Application_Name') or asset.get('application_name'),
                            'cpu_cores': self._parse_int(asset.get('CPU_Cores') or asset.get('cpu_cores')),
                            'memory_gb': self._parse_float(asset.get('Memory_GB') or asset.get('memory_gb')),
                            'storage_gb': self._parse_float(asset.get('Storage_GB') or asset.get('storage_gb'))
                        }
                    }
                    asset_data_list.append(asset_data)
                
                # Create assets in database
                created_assets = await asset_manager.create_assets_from_discovery(
                    discovery_flow_id=discovery_flow_id,
                    asset_data_list=asset_data_list,
                    discovered_in_phase='inventory'
                )
                
                logger.info(f"✅ Successfully persisted {len(created_assets)} assets to database")
                
                # Note: Asset enrichment is now handled by agents using enrichment tools
                # The inventory manager has instructions to enrich assets intelligently
                
                # Update state with created asset information
                asset_ids = [str(asset.id) for asset in created_assets]
                
                # Update asset_inventory field with results
                if hasattr(self.state, 'asset_inventory'):
                    self.state.asset_inventory['created_asset_ids'] = asset_ids
                    self.state.asset_inventory['total_assets'] = len(created_assets)
                    self.state.asset_inventory['status'] = 'completed'
                    self.state.asset_inventory['created_at'] = datetime.utcnow().isoformat()
                
                # Also update asset_creation_results for backward compatibility
                if hasattr(self.state, 'asset_creation_results'):
                    self.state.asset_creation_results['created_asset_ids'] = asset_ids
                    self.state.asset_creation_results['total_created'] = len(created_assets)
                
        except Exception as e:
            logger.error(f"❌ Failed to persist assets to database: {e}", exc_info=True)
    
    def _determine_asset_type(self, asset: Dict[str, Any]) -> str:
        """Determine asset type from asset data with comprehensive classification"""
        asset_type = asset.get('Asset_Type') or asset.get('asset_type') or ''
        asset_name = asset.get('Asset_Name') or asset.get('name') or ''
        
        # Convert to lowercase for comparison
        asset_type_lower = asset_type.lower()
        asset_name_lower = asset_name.lower()
        
        # Server classification
        if ('server' in asset_type_lower or 'host' in asset_type_lower or 
            'vm' in asset_type_lower or 'virtual' in asset_type_lower or
            'linux' in asset_type_lower or 'windows' in asset_type_lower or
            'unix' in asset_type_lower or 'centos' in asset_type_lower or
            'ubuntu' in asset_type_lower or 'redhat' in asset_type_lower):
            return 'server'
        
        # Application classification
        elif ('application' in asset_type_lower or 'app' in asset_type_lower or
              'service' in asset_type_lower or 'software' in asset_type_lower or
              'web' in asset_type_lower or 'api' in asset_type_lower or
              'microservice' in asset_type_lower):
            return 'application'
        
        # Database classification
        elif ('database' in asset_type_lower or 'db' in asset_type_lower or
              'mysql' in asset_type_lower or 'postgresql' in asset_type_lower or
              'oracle' in asset_type_lower or 'sql' in asset_type_lower or
              'mongo' in asset_type_lower or 'redis' in asset_type_lower):
            return 'database'
        
        # Network/Device classification (covers various device types)
        elif ('network' in asset_type_lower or 'device' in asset_type_lower or
              'router' in asset_type_lower or 'switch' in asset_type_lower or
              'firewall' in asset_type_lower or 'load' in asset_type_lower or
              'balancer' in asset_type_lower or 'storage' in asset_type_lower or
              'security' in asset_type_lower or 'infrastructure' in asset_type_lower or
              'appliance' in asset_type_lower):
            return 'device'
        
        # Fallback: check asset name for hints
        elif ('server' in asset_name_lower or 'host' in asset_name_lower or
              'vm' in asset_name_lower):
            return 'server'
        elif ('app' in asset_name_lower or 'service' in asset_name_lower or
              'web' in asset_name_lower):
            return 'application'
        elif ('db' in asset_name_lower or 'database' in asset_name_lower):
            return 'database'
        elif ('device' in asset_name_lower or 'network' in asset_name_lower or
              'router' in asset_name_lower or 'switch' in asset_name_lower):
            return 'device'
        
        # Default classification
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
    
