"""
GCP Asset Collection

Handles asset discovery and collection using Cloud Asset Inventory.
"""

import logging
from typing import Any, Dict, List, Set

from .auth import GCPAuthManager
from .constants import SUPPORTED_ASSET_TYPES
from .dependencies import asset_v1
from .utils import proto_to_dict


class GCPAssetCollector:
    """Collects assets using Cloud Asset Inventory"""
    
    def __init__(self, auth_manager: GCPAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
    async def collect_assets_with_inventory(self, asset_types: Set[str], config: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Use Cloud Asset Inventory to efficiently collect asset data"""
        try:
            asset_data = {}
            parent = f"projects/{self.auth_manager.project_id}"
            
            # Build asset type filters
            asset_type_filters = list(asset_types)
            
            # Request assets with content type RESOURCE
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                asset_types=asset_type_filters,
                content_type=asset_v1.ContentType.RESOURCE,
                page_size=1000
            )
            
            # Execute request and process results
            page_result = self.auth_manager.asset_client.list_assets(request=request)
            
            for asset in page_result:
                asset_type = asset.asset_type
                if asset_type not in asset_data:
                    asset_data[asset_type] = []
                    
                # Convert Asset Inventory result to standard format
                asset_dict = {
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "resource": proto_to_dict(asset.resource) if asset.resource else {},
                    "ancestors": list(asset.ancestors),
                    "update_time": asset.update_time.isoformat() if asset.update_time else None,
                }
                
                # Extract resource data if available
                if asset.resource and asset.resource.data:
                    resource_data = proto_to_dict(asset.resource.data)
                    asset_dict["resource_data"] = resource_data
                    
                asset_data[asset_type].append(asset_dict)
                
            self.logger.info(f"Asset Inventory collected resources across {len(asset_data)} types")
            
            return asset_data
            
        except Exception as e:
            self.logger.error(f"Asset Inventory collection failed: {str(e)}")
            return {}
            
    async def check_asset_type_has_resources(self, asset_type: str) -> bool:
        """Quick check if an asset type has any resources using Asset Inventory"""
        try:
            parent = f"projects/{self.auth_manager.project_id}"
            
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                asset_types=[asset_type],
                page_size=1
            )
            
            page_result = self.auth_manager.asset_client.list_assets(request=request)
            
            # Check if any assets were returned
            for asset in page_result:
                return True
                
            return False
            
        except Exception:
            return False
            
    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available GCP resources for collection
        
        Args:
            configuration: GCP configuration including credentials
            
        Returns:
            List of available asset type identifiers
        """
        try:
            # Use Asset Inventory to quickly check for asset types
            available_types = []
            
            for asset_type in SUPPORTED_ASSET_TYPES:
                try:
                    has_resources = await self.check_asset_type_has_resources(asset_type)
                    if has_resources:
                        available_types.append(asset_type)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to check resources for {asset_type}: {str(e)}")
                    
            return available_types
            
        except Exception as e:
            self.logger.error(f"Failed to get available GCP resources: {str(e)}")
            return []