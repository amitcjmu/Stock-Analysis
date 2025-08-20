"""
Core field mapping route handlers.
Simplified version with modularized components.
"""

import logging

from fastapi import APIRouter

# Import modularized route groups
from .mapping_modules.crud_operations import router as crud_router
from .mapping_modules.analysis_operations import router as analysis_router
from .mapping_modules.utility_operations import router as utility_router

logger = logging.getLogger(__name__)

# Create main router with prefix
router = APIRouter(prefix="/field-mappings")

# Include all modularized routers
router.include_router(crud_router, tags=["Field Mapping CRUD"])
router.include_router(analysis_router, tags=["Field Mapping Analysis"])
router.include_router(utility_router, tags=["Field Mapping Utilities"])

logger.info("Field mapping routes initialized with modular architecture")
