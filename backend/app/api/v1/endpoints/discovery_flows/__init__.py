"""
Discovery Flows Modular Endpoints

This module provides a modular structure for discovery flow API endpoints,
separating concerns into specialized modules:

- Query Endpoints: GET operations for flow status, lists, and information
- Lifecycle Endpoints: POST/DELETE operations for flow creation and deletion
- Execution Endpoints: PUT operations for flow execution and control
- Validation Endpoints: Health checks and validation operations
- Response Mappers: Standardized response formatting
- Status Calculator: Complex status determination logic
"""

import logging

from fastapi import APIRouter

from .execution_endpoints import execution_router
from .lifecycle_endpoints import lifecycle_router
from .query_endpoints import query_router
from .response_mappers import ResponseMappers
from .status_calculator import StatusCalculator
from .validation_endpoints import validation_router

logger = logging.getLogger(__name__)

# Create the main router that combines all specialized routers
router = APIRouter()

# Include all specialized endpoint routers
router.include_router(query_router, prefix="", tags=["discovery-query"])
router.include_router(lifecycle_router, prefix="", tags=["discovery-lifecycle"])
router.include_router(execution_router, prefix="", tags=["discovery-execution"])
router.include_router(validation_router, prefix="", tags=["discovery-validation"])

logger.info("Discovery Flows API - Modular implementation loaded successfully")

__all__ = [
    "router",
    "query_router",
    "lifecycle_router",
    "execution_router",
    "validation_router",
    "ResponseMappers",
    "StatusCalculator",
]
