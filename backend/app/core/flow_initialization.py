"""
Flow Initialization Module

Initializes all flow configurations on application startup.
This ensures all flow types, validators, and handlers are properly registered
before the application starts serving requests.
"""

import logging
from typing import Any, Dict

from app.services.flow_configs import get_flow_summary, initialize_all_flows, verify_flow_configurations

logger = logging.getLogger(__name__)


class FlowInitializer:
    """Manages flow initialization on application startup"""
    
    _initialized = False
    _initialization_results = None
    
    @classmethod
    def initialize(cls) -> Dict[str, Any]:
        """
        Initialize all flow configurations
        
        This should be called once during application startup.
        Subsequent calls will return cached results.
        """
        if cls._initialized and cls._initialization_results:
            logger.info("Flow configurations already initialized")
            return cls._initialization_results
        
        try:
            logger.info("🚀 Initializing Master Flow Orchestrator configurations...")
            
            # Initialize all flows
            init_results = initialize_all_flows()
            
            # Handle already initialized case
            if init_results.get("status") == "already_initialized":
                cls._initialized = True
                cls._initialization_results = init_results
                return init_results
            
            # Log results
            logger.info(f"✅ Registered {len(init_results['flows_registered'])} flow types")
            logger.info(f"✅ Registered {len(init_results['validators_registered'])} validators")
            logger.info(f"✅ Registered {len(init_results['handlers_registered'])} handlers")
            
            if init_results.get("errors"):
                logger.error(f"❌ Initialization errors: {init_results['errors']}")
            
            # Verify configurations
            verification = verify_flow_configurations()
            
            if not verification["consistency_check"]:
                logger.error(f"❌ Configuration verification failed: {verification['issues']}")
            else:
                logger.info("✅ All flow configurations verified successfully")
            
            # Get and log summary
            summary = get_flow_summary()
            logger.info("📊 Flow Configuration Summary:")
            for flow in summary:
                logger.info(f"  - {flow['display_name']} ({flow['name']}): {flow['phase_count']} phases")
            
            # Cache results
            cls._initialized = True
            cls._initialization_results = {
                "initialization": init_results,
                "verification": verification,
                "summary": summary,
                "success": len(init_results.get("errors", [])) == 0 and verification["consistency_check"]
            }
            
            return cls._initialization_results
            
        except Exception as e:
            logger.error(f"❌ Flow initialization failed: {e}", exc_info=True)
            cls._initialization_results = {
                "initialization": {"errors": [str(e)]},
                "verification": {"consistency_check": False, "issues": [str(e)]},
                "summary": [],
                "success": False,
                "error": str(e)
            }
            return cls._initialization_results
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if flows have been initialized"""
        return cls._initialized
    
    @classmethod
    def get_initialization_status(cls) -> Dict[str, Any]:
        """Get detailed initialization status"""
        if not cls._initialized:
            return {
                "initialized": False,
                "message": "Flow configurations not yet initialized"
            }
        
        return {
            "initialized": True,
            "results": cls._initialization_results,
            "flow_count": len(cls._initialization_results.get("summary", [])),
            "success": cls._initialization_results.get("success", False)
        }
    
    @classmethod
    def ensure_initialized(cls) -> None:
        """
        Ensure flows are initialized, raise exception if initialization fails
        
        This can be used as a dependency check in API endpoints
        """
        if not cls._initialized:
            results = cls.initialize()
            if not results.get("success", False):
                raise RuntimeError(
                    f"Flow initialization failed: {results.get('error', 'Unknown error')}"
                )


# Convenience functions
def initialize_flows_on_startup() -> Dict[str, Any]:
    """Initialize flows during application startup"""
    return FlowInitializer.initialize()


def ensure_flows_initialized() -> None:
    """Ensure flows are initialized before processing requests"""
    FlowInitializer.ensure_initialized()


def get_flow_initialization_status() -> Dict[str, Any]:
    """Get current flow initialization status"""
    return FlowInitializer.get_initialization_status()


# Export key items
__all__ = [
    'FlowInitializer',
    'initialize_flows_on_startup',
    'ensure_flows_initialized',
    'get_flow_initialization_status'
]