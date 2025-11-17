"""
Canonical Applications Router Module.

Modularized from router.py to maintain files under 400 lines.
Exports router for backward compatibility.

Structure:
- models.py: Pydantic request/response models
- queries.py: Database query logic (readiness, unmapped assets)
- endpoints.py: Route handlers
- __init__.py: Backward compatibility exports
"""

from fastapi import APIRouter

from app.api.v1.api_tags import APITags

from .. import bulk_mapping
from .endpoints import list_canonical_applications, map_asset_to_application
from .readiness_gaps import get_canonical_application_readiness_gaps

# Create main router
router = APIRouter()

# Include bulk mapping endpoints
router.include_router(bulk_mapping.router, tags=[APITags.CANONICAL_APPLICATIONS])

# Add main endpoints directly to avoid prefix/path conflicts
router.get("", tags=[APITags.CANONICAL_APPLICATIONS])(list_canonical_applications)
router.post("/map-asset", tags=[APITags.CANONICAL_APPLICATIONS])(
    map_asset_to_application
)
router.get(
    "/{canonical_application_id}/readiness-gaps", tags=[APITags.CANONICAL_APPLICATIONS]
)(get_canonical_application_readiness_gaps)

# Export all public symbols for backward compatibility
__all__ = ["router"]
