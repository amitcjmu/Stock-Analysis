"""
Modular field mapping router that combines all field mapping functionality.
This replaces the monolithic field_mapping.py file.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db

from .field_mapping.routes.approval_routes import router as approval_router

# Import all modular routers
from .field_mapping.routes.mapping_routes import router as mapping_router
from .field_mapping.routes.validation_routes import router as validation_router

# Import service dependencies
from .field_mapping.services.mapping_service import MappingService

# Legacy compatibility imports removed - functions are now in modularized routers
# The functions are available through the included routers


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


# Create main router - no prefix needed as mapping_routes has /field-mappings prefix
router = APIRouter()

# Include all sub-routers
router.include_router(
    mapping_router
)  # includes suggestions under /field-mappings prefix
router.include_router(validation_router)
router.include_router(approval_router)

# Note: Legacy routes removed - all functionality available through included routers
# The modularized routers provide all the same endpoints with improved organization


# Health check
@router.get("/health")
async def health_check():
    """Health check for modular field mapping system."""
    return {
        "status": "healthy",
        "service": "field_mapping_modular",
        "modules": [
            "mapping",
            "suggestions",
            "validation",
            "transformation",
            "learning",
        ],
        "legacy_compatibility": False,  # Changed to False since legacy routes removed
    }
