"""
Discovery Flows API - Modular Implementation

This is the new modular implementation of discovery flows endpoints.
The original discovery_flows.py has been refactored into specialized modules:

- Query Endpoints: GET operations for status, lists, and information
- Lifecycle Endpoints: POST/DELETE operations for creation and deletion
- Execution Endpoints: PUT operations for flow execution and control
- Validation Endpoints: Health checks and validation operations
- Response Mappers: Standardized response formatting
- Status Calculator: Complex status determination logic

This provides better separation of concerns, improved maintainability,
and cleaner code organization.
"""

import logging

from fastapi import APIRouter

from .discovery_flows.execution_endpoints import execution_router
from .discovery_flows.lifecycle_endpoints import lifecycle_router

# Import all modular routers
from .discovery_flows.query_endpoints import query_router

# Import response models for OpenAPI documentation
from .discovery_flows.response_mappers import (
    DiscoveryFlowResponse,
    DiscoveryFlowStatusResponse,
    FlowInitializeResponse,
    FlowOperationResponse,
)
from .discovery_flows.validation_endpoints import validation_router

logger = logging.getLogger(__name__)

# Create the main router
router = APIRouter()

# Include all specialized endpoint routers
router.include_router(query_router, prefix="", tags=["discovery-query"])
router.include_router(lifecycle_router, prefix="", tags=["discovery-lifecycle"])
router.include_router(execution_router, prefix="", tags=["discovery-execution"])
router.include_router(validation_router, prefix="", tags=["discovery-validation"])


# Export models for OpenAPI documentation
__all__ = [
    "router",
    "DiscoveryFlowResponse",
    "DiscoveryFlowStatusResponse",
    "FlowInitializeResponse",
    "FlowOperationResponse",
]

# Log the modular implementation startup
logger.info("Discovery Flows API - Modular implementation loaded successfully")
logger.info("Available modules: query, lifecycle, execution, validation")
logger.info("Total endpoints: ~25 endpoints across 4 specialized modules")
