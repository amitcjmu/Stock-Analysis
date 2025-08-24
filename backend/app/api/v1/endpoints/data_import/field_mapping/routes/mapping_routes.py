"""
Core field mapping route handlers.
Simplified version with modularized components.
"""

import logging

from fastapi import APIRouter

from backend.app.api.v1.api_tags import APITags
from .mapping_modules.analysis_operations import router as analysis_router

# Import modularized route groups
from .mapping_modules.crud_operations import router as crud_router
from .mapping_modules.learning_operations import router as learning_router
from .mapping_modules.utility_operations import router as utility_router

logger = logging.getLogger(__name__)

# Create main router with prefix
router = APIRouter(prefix="/field-mappings")

# Include all modularized routers
router.include_router(crud_router, tags=[APITags.FIELD_MAPPING_CRUD])
router.include_router(analysis_router, tags=[APITags.FIELD_MAPPING_ANALYSIS])
router.include_router(utility_router, tags=[APITags.FIELD_MAPPING_UTILITIES])
router.include_router(learning_router, tags=[APITags.AI_LEARNING])

logger.info(
    "Field mapping routes initialized with modular architecture including learning operations"
)
