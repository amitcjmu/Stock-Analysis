"""
Planning endpoints module (MFO-integrated).

MFO-integrated planning flow endpoints following Assessment Flow pattern.
Implements wave planning, resource allocation, timeline generation, and cost estimation.

Related ADRs:
- ADR-006: Master Flow Orchestrator
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
"""

from fastapi import APIRouter

from .initialize import router as initialize_router
from .execute import router as execute_router
from .status import router as status_router
from .update import router as update_router
from .export import router as export_router

# Create main router that combines all sub-routers
router = APIRouter()

# Include all sub-routers (order matters for route precedence)
router.include_router(initialize_router)
router.include_router(execute_router)
router.include_router(status_router)
router.include_router(update_router)
router.include_router(export_router)

# Export for backward compatibility
__all__ = ["router"]
