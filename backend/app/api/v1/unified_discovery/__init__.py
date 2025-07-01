"""
Unified Discovery Module

Modularized unified discovery functionality with clear separation:
- routes/: HTTP route handlers for flow management, execution, monitoring
- services/: Business logic services for discovery orchestration
- middleware/: Request processing and compatibility layers
- integrations/: External service integrations and adapters
"""

from .routes.flow_routes import router as flow_router
from .routes.import_routes import router as import_router
from .routes.status_routes import router as status_router
from .routes.websocket_routes import router as websocket_router

from .services.discovery_orchestrator import DiscoveryOrchestrator
from .services.flow_coordinator import FlowCoordinator
from .services.compatibility_service import CompatibilityService

__all__ = [
    'flow_router',
    'import_router', 
    'status_router',
    'websocket_router',
    'DiscoveryOrchestrator',
    'FlowCoordinator',
    'CompatibilityService'
]