"""
Assessment Flow API endpoints for v1 API.
Simplified version with modularized components.

This module serves as the main router/facade for assessment flow operations,
delegating to modular components while maintaining 100% backward compatibility.
"""

import logging

from fastapi import APIRouter

# Import modularized routers
from .assessment_flow.flow_management import router as flow_management_router
from .assessment_flow.architecture_standards import router as architecture_router
from .assessment_flow.component_analysis import router as component_router
from .assessment_flow.tech_debt_analysis import router as tech_debt_router
from .assessment_flow.sixr_decisions import router as sixr_router
from .assessment_flow.finalization import router as finalization_router

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include all modularized routers
router.include_router(flow_management_router, tags=["Assessment Flow Management"])
router.include_router(architecture_router, tags=["Architecture Standards"])
router.include_router(component_router, tags=["Component Analysis"])
router.include_router(tech_debt_router, tags=["Tech Debt Analysis"])
router.include_router(sixr_router, tags=["6R Decisions"])
router.include_router(finalization_router, tags=["Flow Finalization"])

logger.info("Assessment Flow API endpoints initialized with modular architecture")
