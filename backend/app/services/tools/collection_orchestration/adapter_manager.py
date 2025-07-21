"""
Platform Adapter Manager

Manages platform adapters for automated data collection.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from app.services.collection_flow import adapter_registry
from .base import BaseCollectionTool

logger = logging.getLogger(__name__)


class PlatformAdapterManager(AsyncBaseDiscoveryTool, BaseCollectionTool):
    """Manages platform adapters for automated collection"""
    
    name: str = "PlatformAdapterManager"
    description: str = "Coordinate and manage platform adapters for data collection"
    
    def __init__(self):
        super().__init__()
        self.name = "PlatformAdapterManager"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="PlatformAdapterManager",
            description="Manages platform adapters for automated collection",
            tool_class=cls,
            categories=["collection", "adapter", "orchestration"],
            required_params=["platforms", "action"],
            optional_params=["adapter_configs", "credentials"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        platforms: List[Dict[str, Any]],
        action: str,
        adapter_configs: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage platform adapters for collection.
        
        Args:
            platforms: List of detected platforms
            action: Action to perform (initialize, execute, status, cleanup)
            adapter_configs: Platform-specific adapter configurations
            credentials: Platform credentials for authentication
            
        Returns:
            Adapter management results
        """
        result = self._create_base_result(action)
        result["adapters"] = []
        
        try:
            if action == "initialize":
                await self._initialize_adapters(platforms, result)
            elif action == "execute":
                await self._execute_collections(platforms, adapter_configs, credentials, result)
            elif action == "status":
                await self._get_adapter_status(platforms, result)
            elif action == "cleanup":
                await self._cleanup_adapters(platforms, result)
            else:
                self._add_error(result, f"Unknown action: {action}")
                return result
            
            self._mark_success(result)
            return result
            
        except Exception as e:
            self._add_error(result, f"Platform adapter management failed: {str(e)}")
            return result
    
    async def _initialize_adapters(self, platforms: List[Dict[str, Any]], result: Dict[str, Any]):
        """Initialize adapters for each platform"""
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            adapter = adapter_registry.get_adapter(platform_type)
            
            if adapter:
                adapter_info = {
                    "platform": platform_type,
                    "name": platform.get("name"),
                    "status": "initialized",
                    "capabilities": adapter.get_capabilities() if hasattr(adapter, 'get_capabilities') else []
                }
                result["adapters"].append(adapter_info)
            else:
                self._add_error(result, f"No adapter found for platform: {platform_type}")
    
    async def _execute_collections(
        self, 
        platforms: List[Dict[str, Any]], 
        adapter_configs: Optional[Dict[str, Any]], 
        credentials: Optional[Dict[str, Any]], 
        result: Dict[str, Any]
    ):
        """Execute collection using adapters"""
        collection_tasks = []
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            adapter = adapter_registry.get_adapter(platform_type)
            
            if adapter:
                config = adapter_configs.get(platform_type, {}) if adapter_configs else {}
                creds = credentials.get(platform_type, {}) if credentials else {}
                
                # Create collection task
                task = self._collect_with_adapter(adapter, platform, config, creds)
                collection_tasks.append(task)
        
        # Execute collections in parallel
        if collection_tasks:
            collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            for i, collection_result in enumerate(collection_results):
                if isinstance(collection_result, Exception):
                    self._add_error(result, f"Collection failed for {platforms[i]['name']}: {str(collection_result)}")
                else:
                    result["adapters"].append(collection_result)
    
    async def _get_adapter_status(self, platforms: List[Dict[str, Any]], result: Dict[str, Any]):
        """Get status of active collections"""
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            adapter = adapter_registry.get_adapter(platform_type)
            
            if adapter and hasattr(adapter, 'get_status'):
                status = await adapter.get_status()
                result["adapters"].append({
                    "platform": platform_type,
                    "status": status
                })
    
    async def _cleanup_adapters(self, platforms: List[Dict[str, Any]], result: Dict[str, Any]):
        """Clean up adapter resources"""
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            adapter = adapter_registry.get_adapter(platform_type)
            
            if adapter and hasattr(adapter, 'cleanup'):
                await adapter.cleanup()
                result["adapters"].append({
                    "platform": platform_type,
                    "status": "cleaned_up"
                })
    
    async def _collect_with_adapter(
        self,
        adapter: Any,
        platform: Dict[str, Any],
        config: Dict[str, Any],
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute collection with a single adapter"""
        try:
            # Initialize adapter with credentials
            if hasattr(adapter, 'initialize'):
                await adapter.initialize(credentials)
            
            # Execute collection
            if hasattr(adapter, 'collect_data'):
                data = await adapter.collect_data(config)
            else:
                data = await adapter.collect()
            
            return {
                "platform": platform.get("type"),
                "name": platform.get("name"),
                "status": "collected",
                "data_count": len(data) if isinstance(data, list) else 1,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Collection failed for {platform.get('name')}: {str(e)}")
            raise