"""
Asset Inventory Phase

Handles the asset inventory phase of the discovery flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# from app.services.agents.asset_inventory_agent import AssetInventoryAgent
# TODO: Replace with real CrewAI agent
from ..flow_config import PhaseNames, FlowConfig

logger = logging.getLogger(__name__)


class AssetInventoryPhase:
    """Handles asset inventory phase execution"""
    
    def __init__(self, state, asset_inventory_agent, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize asset inventory phase
        
        Args:
            state: The flow state object
            asset_inventory_agent: The asset inventory agent instance
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.asset_inventory_agent = asset_inventory_agent
        self._init_context = init_context
        self.flow_bridge = flow_bridge
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the asset inventory phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        logger.info("🤖 Starting Asset Inventory with Agent-First Architecture")
        self.state.current_phase = PhaseNames.ASSET_INVENTORY
        
        # Update database immediately when phase starts
        await self._update_flow_state()
        
        try:
            # Create discovery assets from cleaned data
            assets = await self._create_discovery_assets()
            
            # Store results
            self.state.asset_inventory = {
                "assets": assets,
                "total_count": len(assets),
                "asset_types": self._categorize_assets(assets)
            }
            
            # Update phase completion
            self.state.phase_completion['inventory'] = True
            self.state.progress_percentage = 80.0
            # Update total_assets in the asset_inventory dictionary
            self.state.asset_inventory["total_assets"] = len(assets)
            
            # Persist state
            await self._update_flow_state()
            
            logger.info(f"✅ Asset inventory completed with {len(assets)} assets")
            return "asset_inventory_completed"
            
        except Exception as e:
            logger.error(f"❌ Asset inventory failed: {e}")
            self.state.add_error("asset_inventory", f"Failed to create assets: {str(e)}")
            
            # Update database even on failure
            await self._update_flow_state()
            
            return "asset_inventory_failed"
    
    async def _create_discovery_assets(self) -> List[Dict[str, Any]]:
        """Create discovery assets from cleaned data"""
        cleaned_data = self.state.cleaned_data or self.state.raw_data
        field_mappings = self.state.field_mappings.get('mappings', {})
        
        assets = []
        for index, record in enumerate(cleaned_data):
            # Apply field mappings
            mapped_data = self._apply_field_mappings(record, field_mappings)
            
            # Create asset
            asset = {
                "name": self._extract_asset_name(mapped_data, record, index),
                "type": self._determine_asset_type(mapped_data, record),
                "data": mapped_data,
                "original_data": record,
                "created_at": datetime.utcnow().isoformat()
            }
            assets.append(asset)
        
        return assets
    
    def _apply_field_mappings(self, record: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mappings to a record"""
        mapped_data = {}
        for source_field, target_field in field_mappings.items():
            if source_field in record:
                mapped_data[target_field] = record[source_field]
        return mapped_data
    
    def _extract_asset_name(self, mapped_data: Dict[str, Any], original_data: Dict[str, Any], index: int) -> str:
        """Extract asset name from data"""
        # Try common name fields
        for field in ['name', 'asset_name', 'hostname', 'server_name', 'application_name']:
            if field in mapped_data:
                return str(mapped_data[field])
            if field in original_data:
                return str(original_data[field])
        
        # Fallback to index
        return f"Asset_{index + 1}"
    
    def _determine_asset_type(self, mapped_data: Dict[str, Any], original_data: Dict[str, Any]) -> str:
        """Determine asset type from data"""
        # Check mapped data first
        if 'type' in mapped_data:
            return str(mapped_data['type']).lower()
        if 'asset_type' in mapped_data:
            return str(mapped_data['asset_type']).lower()
        
        # Check original data
        if 'type' in original_data:
            return str(original_data['type']).lower()
        
        # Try to infer from keywords
        data_str = str(mapped_data).lower() + str(original_data).lower()
        for asset_type, keywords in FlowConfig.ASSET_TYPE_KEYWORDS.items():
            if any(keyword in data_str for keyword in keywords):
                return asset_type
        
        return 'unknown'
    
    def _categorize_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize assets by type"""
        categories = {}
        for asset in assets:
            asset_type = asset.get('type', 'unknown')
            categories[asset_type] = categories.get(asset_type, 0) + 1
        return categories
    
    async def _update_flow_state(self):
        """Update flow state in database"""
        if self.flow_bridge:
            try:
                await self.flow_bridge.update_flow_state(self.state)
            except Exception as e:
                logger.warning(f"⚠️ Failed to update flow state: {e}")