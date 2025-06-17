"""
Core Import Module - Modular data upload and import session management.
Delegates to specialized handlers following the modular handler pattern.
"""

import logging
from fastapi import APIRouter

# Import modular handlers
from .handlers.clean_api_handler import router as clean_api_router
from .handlers.legacy_upload_handler import router as legacy_upload_router
from .handlers.import_retrieval_handler import router as import_retrieval_router
from .handlers.import_storage_handler import router as import_storage_router

logger = logging.getLogger(__name__)

# Create main router for data import
router = APIRouter()

# Include all handler routers with proper prefixes
router.include_router(clean_api_router, tags=["Clean API"])
router.include_router(legacy_upload_router, tags=["Legacy Upload"])
router.include_router(import_retrieval_router, tags=["Import Retrieval"])
router.include_router(import_storage_router, tags=["Import Storage"])

# Health check endpoint for the modular service
@router.get("/health")
async def health_check():
    """Health check for the modular data import service."""
    return {
        "service": "core_import_modular",
        "status": "healthy",
        "handlers": [
            "clean_api_handler",
            "legacy_upload_handler", 
            "import_retrieval_handler",
            "import_storage_handler"
        ],
        "message": "All import handlers are loaded and ready"
    } 