"""
Phase 2: AI-Enhanced Gap Analysis Endpoints

Modularized structure for maintainability:
- gap_analysis_handlers.py: POST /analyze-gaps endpoint
- background_workers.py: Background job processing
- progress_handlers.py: GET /enhancement-progress endpoint
- job_state_manager.py: Redis job state management

This module provides backward compatibility by exporting the router.
"""

from fastapi import APIRouter

from .gap_analysis_handlers import analyze_gaps
from .progress_handlers import get_enhancement_progress

# Create router for this module
router = APIRouter()

# Register endpoint handlers
router.add_api_route(
    "/{flow_id}/analyze-gaps", analyze_gaps, methods=["POST"], status_code=202
)
router.add_api_route(
    "/{flow_id}/enhancement-progress", get_enhancement_progress, methods=["GET"]
)

# Export router for backward compatibility
__all__ = ["router"]
