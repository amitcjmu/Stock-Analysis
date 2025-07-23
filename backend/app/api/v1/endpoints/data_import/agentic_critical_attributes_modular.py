"""
Modular agentic critical attributes router that combines all functionality.
This replaces the monolithic agentic_critical_attributes.py file.
"""

from fastapi import APIRouter

# Import all modular routers
from .agentic_critical_attributes.routes.analysis_routes import (
    router as analysis_router,
)
from .agentic_critical_attributes.routes.feedback_routes import (
    router as feedback_router,
)
from .agentic_critical_attributes.routes.suggestion_routes import (
    router as suggestion_router,
)

# Create main router
router = APIRouter(
    prefix="/agentic-critical-attributes", tags=["agentic-critical-attributes"]
)

# Include all sub-routers
router.include_router(analysis_router)
router.include_router(suggestion_router)
router.include_router(feedback_router)

# Legacy compatibility routes - these delegate to the new modular structure
from .agentic_critical_attributes.routes.analysis_routes import (
    get_agentic_critical_attributes as legacy_get_analysis,
)
from .agentic_critical_attributes.routes.analysis_routes import (
    trigger_field_mapping_crew_analysis as legacy_trigger_crew,
)


# Add legacy routes for backward compatibility
@router.get("/agentic-critical-attributes")
async def get_agentic_critical_attributes_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_get_analysis(**kwargs)


@router.post("/trigger-field-mapping-crew")
async def trigger_field_mapping_crew_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_trigger_crew(**kwargs)


# Health check
@router.get("/health")
async def health_check():
    """Health check for modular agentic critical attributes system."""
    return {
        "status": "healthy",
        "service": "agentic_critical_attributes_modular",
        "modules": ["analysis", "suggestions", "feedback", "learning"],
        "legacy_compatibility": True,
        "ai_capabilities": ["crewai_agents", "fallback_analysis", "learning_feedback"],
    }
