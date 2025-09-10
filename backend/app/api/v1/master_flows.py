"""
Master Flow Coordination API Endpoints - Facade Router
Task 5.2.1: API endpoints for cross-phase asset queries and master flow analytics

This module acts as a facade router that imports and combines endpoints from
the modularized master flows components for backward compatibility.
"""

import logging
from fastapi import APIRouter

# Import sub-routers from modularized components
from app.api.v1.master_flows.master_flows_analytics import router as analytics_router
from app.api.v1.master_flows.master_flows_assessment import router as assessment_router
from app.api.v1.master_flows.master_flows_crud import router as crud_router

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include all sub-routers to maintain backward compatibility
# All endpoints will be available at the same URLs as before
router.include_router(analytics_router, tags=["Master Flow Coordination"])
router.include_router(assessment_router, tags=["Master Flow Coordination"])
router.include_router(crud_router, tags=["Master Flow Coordination"])

logger.info("Master Flows facade router configured with modular endpoints")
