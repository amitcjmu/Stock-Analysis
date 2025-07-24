"""
Modular field mapping router that combines all field mapping functionality.
This replaces the monolithic field_mapping.py file.
"""

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .field_mapping.routes.approval_routes import router as approval_router

# Import all modular routers
from .field_mapping.routes.mapping_routes import router as mapping_router
from .field_mapping.routes.suggestion_routes import router as suggestion_router
from .field_mapping.routes.validation_routes import router as validation_router

# Import service dependencies
from .field_mapping.services.mapping_service import MappingService


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


# Create main router
router = APIRouter(prefix="/field-mapping", tags=["field-mapping"])

# Include all sub-routers
router.include_router(mapping_router)
router.include_router(suggestion_router)
router.include_router(validation_router)
router.include_router(approval_router)

# Legacy compatibility routes - these delegate to the new modular structure
from .field_mapping.routes.mapping_routes import (
    create_field_mapping_latest as legacy_create_latest,
)
from .field_mapping.routes.mapping_routes import (
    generate_field_mappings as legacy_generate,
)
from .field_mapping.routes.mapping_routes import (
    get_field_mappings as legacy_get_mappings,
)
from .field_mapping.routes.suggestion_routes import (
    get_available_target_fields as legacy_get_available_fields,
)
from .field_mapping.routes.suggestion_routes import (
    get_field_mapping_suggestions as legacy_get_suggestions,
)


# Add legacy routes for backward compatibility
@router.get("/imports/{import_id}/field-mappings")
async def get_field_mappings_legacy(
    import_id: str, service: MappingService = Depends(get_mapping_service)
):
    """Legacy compatibility route."""
    return await legacy_get_mappings(import_id, service)


@router.post("/imports/{import_id}/field-mappings")
async def create_field_mappings_legacy(import_id: str, **kwargs):
    """Legacy compatibility route."""
    return await legacy_generate(import_id, **kwargs)


@router.post("/imports/latest/field-mappings")
async def create_field_mapping_latest_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_create_latest(**kwargs)


@router.get("/imports/{import_id}/field-mapping-suggestions")
async def get_field_mapping_suggestions_legacy(import_id: str, **kwargs):
    """Legacy compatibility route."""
    return await legacy_get_suggestions(import_id, **kwargs)


@router.get("/available-target-fields")
async def get_available_target_fields_legacy(**kwargs):
    """Legacy compatibility route."""
    return await legacy_get_available_fields(**kwargs)


# Health check
@router.get("/health")
async def health_check():
    """Health check for modular field mapping system."""
    return {
        "status": "healthy",
        "service": "field_mapping_modular",
        "modules": ["mapping", "suggestions", "validation", "transformation"],
        "legacy_compatibility": True,
    }
