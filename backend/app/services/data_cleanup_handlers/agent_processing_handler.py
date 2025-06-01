"""
Agent Processing Handler
Handles agent-driven data processing and cleanup operations.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AgentProcessingHandler:
    """Handler for agent-driven data processing operations."""
    
    def __init__(self):
        self.agent_intelligence_available = True
    
    def is_available(self) -> bool:
        """Check if the handler is available."""
        return True
    
    async def process_data_cleanup(self, asset_data: List[Dict[str, Any]], 
                                 agent_operations: List[Dict[str, Any]],
                                 user_preferences: Dict[str, Any],
                                 client_account_id: Optional[str] = None,
                                 engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Agent-driven data processing with intelligent cleanup operations.
        """
        try:
            # Try agent-driven processing first
            if self.agent_intelligence_available:
                try:
                    # Import agent communication service
                    from app.services.agent_ui_bridge import AgentUIBridge
                    
                    agent_bridge = AgentUIBridge()
                    
                    # Prepare cleanup request for agents
                    cleanup_request = {
                        "data_source": {
                            "assets": asset_data,
                            "total_count": len(asset_data),
                            "context": "data_cleanup_processing"
                        },
                        "operations": agent_operations,
                        "user_preferences": user_preferences,
                        "analysis_type": "data_cleanup_processing",
                        "page_context": "data-cleansing",
                        "client_context": {
                            "client_account_id": client_account_id,
                            "engagement_id": engagement_id
                        }
                    }
                    
                    # Get agent-driven cleanup
                    agent_response = await agent_bridge.process_with_agents(cleanup_request)
                    
                    if agent_response.get("status") == "success":
                        return {
                            "status": "success",
                            "processing_type": "agent_driven",
                            "cleaned_assets": agent_response.get("processed_assets", asset_data),
                            "quality_improvement": agent_response.get("quality_improvement", {}),
                            "operations_applied": agent_response.get("operations_applied", []),
                            "quality_metrics": agent_response.get("quality_metrics", {}),
                            "agent_confidence": agent_response.get("confidence", 0.85),
                            "processing_summary": agent_response.get("processing_summary", "Agent processing completed")
                        }
                    
                except Exception as e:
                    logger.warning(f"Agent processing failed, using fallback: {e}")
                    self.agent_intelligence_available = False
            
            # Fallback to rule-based processing
            return await self._fallback_data_processing(asset_data, agent_operations, user_preferences)
            
        except Exception as e:
            logger.error(f"Error in process_data_cleanup: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_type": "error"
            }

    async def _fallback_data_processing(self, asset_data: List[Dict[str, Any]], 
                                      agent_operations: List[Dict[str, Any]],
                                      user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processing using rule-based operations."""
        logger.info("Using fallback rule-based data processing")
        
        processed_assets = []
        operations_applied = []
        
        for asset in asset_data:
            processed_asset = asset.copy()
            asset_operations = []
            
            # Apply basic cleanup operations
            for operation in agent_operations:
                op_type = operation.get("operation", "")
                
                if op_type == "standardize_asset_types":
                    processed_asset = self._standardize_asset_type(processed_asset)
                    asset_operations.append("standardize_asset_types")
                
                elif op_type == "normalize_environments":
                    processed_asset = self._normalize_environment(processed_asset)
                    asset_operations.append("normalize_environments")
                
                elif op_type == "fix_hostname_format":
                    processed_asset = self._fix_hostname_format(processed_asset)
                    asset_operations.append("fix_hostname_format")
            
            processed_assets.append(processed_asset)
            if asset_operations:
                operations_applied.extend(asset_operations)
        
        return {
            "status": "success",
            "processing_type": "fallback_rules",
            "cleaned_assets": processed_assets,
            "quality_improvement": {"processed_count": len(processed_assets)},
            "operations_applied": list(set(operations_applied)),
            "quality_metrics": {"improvement_score": 15},
            "agent_confidence": 0.6,
            "processing_summary": f"Applied fallback processing to {len(processed_assets)} assets"
        }

    async def process_agent_driven_cleanup(self, asset_data: List[Dict[str, Any]], 
                                         agent_operations: List[Dict[str, Any]],
                                         user_preferences: Dict[str, Any] = None,
                                         client_account_id: Optional[str] = None,
                                         engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """Process agent-driven cleanup operations on asset data."""
        if user_preferences is None:
            user_preferences = {}
            
        # Use the main processing method
        return await self.process_data_cleanup(
            asset_data, agent_operations, user_preferences, client_account_id, engagement_id
        )

    def _standardize_asset_type(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize asset type values."""
        asset_type = str(asset.get("asset_type", "")).lower().strip()
        
        # Standard mappings
        type_mappings = {
            "server": "SERVER",
            "srv": "SERVER", 
            "host": "SERVER",
            "db": "DATABASE",
            "database": "DATABASE",
            "app": "APPLICATION",
            "application": "APPLICATION",
            "net": "NETWORK",
            "network": "NETWORK",
            "storage": "STORAGE",
            "stor": "STORAGE"
        }
        
        standardized_type = type_mappings.get(asset_type, asset.get("asset_type", "UNKNOWN"))
        asset["asset_type"] = standardized_type
        return asset

    def _normalize_environment(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment values."""
        environment = str(asset.get("environment", "")).lower().strip()
        
        # Standard mappings
        env_mappings = {
            "prod": "production",
            "production": "production",
            "prd": "production",
            "dev": "development", 
            "development": "development",
            "test": "testing",
            "testing": "testing",
            "tst": "testing",
            "stage": "staging",
            "staging": "staging",
            "stg": "staging"
        }
        
        normalized_env = env_mappings.get(environment, asset.get("environment", "unknown"))
        asset["environment"] = normalized_env
        return asset

    def _fix_hostname_format(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix hostname formatting issues."""
        hostname = asset.get("hostname", "")
        if hostname:
            # Convert to lowercase and remove invalid characters
            hostname = str(hostname).lower().strip()
            hostname = ''.join(c for c in hostname if c.isalnum() or c in '-_.')
            asset["hostname"] = hostname
        return asset 