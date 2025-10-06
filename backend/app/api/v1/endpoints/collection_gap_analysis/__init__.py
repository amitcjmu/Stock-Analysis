"""
Two-Phase Gap Analysis API Router

Implements programmatic gap scanning (Phase 1) and AI-enhanced analysis (Phase 2).
Per ADR-006, all flows must integrate with Master Flow Orchestrator.

Modularized structure:
- scan_endpoints.py: POST /scan-gaps (Phase 1 programmatic scanning)
- analysis_endpoints.py: POST /analyze-gaps (Phase 2 AI enhancement)
- update_endpoints.py: PUT /update-gaps, GET /gaps (manual edits and queries)
- utils.py: Shared helper functions
"""

from fastapi import APIRouter

from .analysis_endpoints import router as analysis_router
from .scan_endpoints import router as scan_router
from .update_endpoints import router as update_router

# Create main router with prefix
router = APIRouter(
    prefix="/collection/flows",
)

# Include all endpoint routers
router.include_router(scan_router, tags=["Collection Gap Analysis"])
router.include_router(analysis_router, tags=["Collection Gap Analysis"])
router.include_router(update_router, tags=["Collection Gap Analysis"])

# Export router for backward compatibility
__all__ = ["router"]
