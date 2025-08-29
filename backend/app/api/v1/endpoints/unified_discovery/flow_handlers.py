"""
Flow Management Handlers for Unified Discovery

Modularized flow handlers for better maintainability while maintaining backward compatibility.
This file serves as a facade that imports from specialized handler modules.

Modules:
- flow_schemas: Request and response models
- flow_initialization_handlers: Flow initialization endpoints
- flow_status_handlers: Flow status and active flow endpoints
- flow_execution_handlers: Flow execution endpoints
- flow_control_handlers: Flow control operations (pause/resume/delete/retry)
"""

from fastapi import APIRouter

# Import all routers from modularized handlers
from .flow_initialization_handlers import router as init_router
from .flow_status_handlers import router as status_router
from .flow_execution_handlers import router as execution_router
from .flow_control_handlers import router as control_router

# Import schemas for backward compatibility
from .flow_schemas import FlowInitializationRequest, FlowInitializationResponse

# Create main router and include all specialized routers
router = APIRouter()

# Include all modular routers (maintaining all original functionality)
router.include_router(init_router)
router.include_router(status_router)
router.include_router(execution_router)
router.include_router(control_router)

# IMPORTANT: All flow resource endpoints use PLURAL /flows/ convention
# Action endpoints (like flow-processing) may differ

__all__ = [
    "router",
    "FlowInitializationRequest",
    "FlowInitializationResponse",
]
