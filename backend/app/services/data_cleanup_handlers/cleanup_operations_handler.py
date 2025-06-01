"""
Cleanup Operations Handler
Handles batch cleanup operations and standard cleanup functions.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class CleanupOperationsHandler:
    """Handler for cleanup operations and batch processing."""
    
    def __init__(self):
        pass
    
    def is_available(self) -> bool:
        """Check if the handler is available."""
        return True
    
    async def process_data_cleanup_batch(self, asset_data: List[Dict[str, Any]], 
                                       cleanup_operations: List[str],
                                       client_account_id: Optional[str] = None,
                                       engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """Process data cleanup in batches."""
        logger.info(f"Processing batch cleanup for {len(asset_data)} assets with {len(cleanup_operations)} operations")
        
        processed_assets = []
        quality_improvements = {"assets_improved": 0, "total_improvements": 0}
        
        for asset in asset_data:
            processed_asset = self._apply_cleanup_operations(asset, cleanup_operations)
            processed_assets.append(processed_asset)
            
            # Track improvements
            if processed_asset != asset:
                quality_improvements["assets_improved"] += 1
        
        return {
            "status": "success",
            "total_assets": len(asset_data),
            "processed_assets": processed_assets,
            "quality_improvements": quality_improvements,
            "operations_applied": cleanup_operations,
            "summary": f"Processed {len(processed_assets)} assets with {len(cleanup_operations)} operations"
        }
    
    def _apply_cleanup_operations(self, asset: Dict[str, Any], operations: List[str]) -> Dict[str, Any]:
        """Apply cleanup operations to a single asset."""
        processed_asset = asset.copy()
        
        for operation in operations:
            if operation == "standardize_asset_type":
                processed_asset = self._standardize_asset_type(processed_asset)
            elif operation == "normalize_environment":
                processed_asset = self._normalize_environment(processed_asset)
            elif operation == "fix_hostname_format":
                processed_asset = self._fix_hostname_format(processed_asset)
            elif operation == "complete_missing_fields":
                processed_asset = self._complete_missing_fields(processed_asset)
        
        return processed_asset
    
    def _standardize_asset_type(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize asset type values."""
        asset_type = str(asset.get("asset_type", "")).lower().strip()
        
        type_mappings = {
            "server": "SERVER", "srv": "SERVER", "host": "SERVER",
            "db": "DATABASE", "database": "DATABASE",
            "app": "APPLICATION", "application": "APPLICATION",
            "net": "NETWORK", "network": "NETWORK",
            "storage": "STORAGE", "stor": "STORAGE"
        }
        
        standardized_type = type_mappings.get(asset_type, asset.get("asset_type", "UNKNOWN"))
        asset["asset_type"] = standardized_type
        return asset
    
    def _normalize_environment(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment values."""
        environment = str(asset.get("environment", "")).lower().strip()
        
        env_mappings = {
            "prod": "production", "production": "production", "prd": "production",
            "dev": "development", "development": "development",
            "test": "testing", "testing": "testing", "tst": "testing",
            "stage": "staging", "staging": "staging", "stg": "staging"
        }
        
        normalized_env = env_mappings.get(environment, asset.get("environment", "unknown"))
        asset["environment"] = normalized_env
        return asset
    
    def _fix_hostname_format(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix hostname formatting issues."""
        hostname = asset.get("hostname", "")
        if hostname:
            hostname = str(hostname).lower().strip()
            hostname = ''.join(c for c in hostname if c.isalnum() or c in '-_.')
            asset["hostname"] = hostname
        return asset
    
    def _complete_missing_fields(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Complete missing fields with default values."""
        if not asset.get("asset_name") and asset.get("hostname"):
            asset["asset_name"] = asset["hostname"]
        
        if not asset.get("business_criticality"):
            asset["business_criticality"] = "medium"
        
        if not asset.get("environment"):
            asset["environment"] = "unknown"
        
        return asset 