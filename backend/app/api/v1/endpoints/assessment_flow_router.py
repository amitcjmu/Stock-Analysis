"""
Assessment Flow API endpoints for v1 API.
Simplified version with modularized components.

This module serves as the main router/facade for assessment flow operations,
delegating to modular components while maintaining 100% backward compatibility.
"""

import logging

from fastapi import APIRouter
from app.api.v1.api_tags import APITags

# Import modularized routers
from .assessment_flow.flow_management import router as flow_management_router
from .assessment_flow.asset_resolution import router as asset_resolution_router
from .assessment_flow.architecture_standards import router as architecture_router
from .assessment_flow.component_analysis import router as component_router
from .assessment_flow.tech_debt_analysis import router as tech_debt_router
from .assessment_flow.sixr_decisions import router as sixr_router
from .assessment_flow.finalization import router as finalization_router

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include all modularized routers
router.include_router(flow_management_router, tags=[APITags.ASSESSMENT_FLOW_MANAGEMENT])
router.include_router(asset_resolution_router, tags=[APITags.ASSET_RESOLUTION])
router.include_router(architecture_router, tags=[APITags.ARCHITECTURE_STANDARDS])
router.include_router(component_router, tags=[APITags.COMPONENT_ANALYSIS])
router.include_router(tech_debt_router, tags=[APITags.TECH_DEBT_ANALYSIS])
router.include_router(sixr_router, tags=[APITags.SIXR_DECISIONS])
router.include_router(finalization_router, tags=[APITags.FLOW_FINALIZATION])

logger.info("Assessment Flow API endpoints initialized with modular architecture")
