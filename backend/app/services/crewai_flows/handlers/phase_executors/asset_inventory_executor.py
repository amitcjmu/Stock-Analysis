"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.
"""

from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor


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
        return self._process_crew_result(crew_result)
    
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
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        raw_data = getattr(self.state, 'raw_data', [])
        
        logger.info(f"🔍 Asset inventory crew input: {len(cleaned_data)} cleaned_data, {len(raw_data)} raw_data")
        
        return {"cleaned_data": cleaned_data}
    
    def _store_results(self, results: Dict[str, Any]):
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