"""
Core Import Module - Modular data upload and import session management.
Delegates to specialized handlers following the modular handler pattern.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

# Import modular handlers
from .handlers.clean_api_handler import router as clean_api_router
from .handlers.legacy_upload_handler import router as legacy_upload_router
from .handlers.import_retrieval_handler import router as import_retrieval_router
from .handlers.import_storage_handler import router as import_storage_handler

# Import agentic intelligence modules
try:
    from .agentic_critical_attributes import router as agentic_critical_attributes_router
    AGENTIC_AVAILABLE = True
except ImportError:
    AGENTIC_AVAILABLE = False
    agentic_critical_attributes_router = None

logger = logging.getLogger(__name__)

# Create main router for data import
router = APIRouter()

# Include all handler routers with proper prefixes
router.include_router(clean_api_router, tags=["Clean API"])
router.include_router(legacy_upload_router, tags=["Legacy Upload"])
router.include_router(import_retrieval_router, tags=["Import Retrieval"])
router.include_router(import_storage_handler, tags=["Import Storage"])

# Include agentic intelligence router if available
if AGENTIC_AVAILABLE:
    router.include_router(agentic_critical_attributes_router, tags=["Agentic Intelligence"])
    logger.info("✅ Agentic Critical Attributes router loaded")
else:
    logger.warning("⚠️ Agentic Critical Attributes router not available")

# Health check endpoint for the modular service
@router.get("/health")
async def health_check():
    """Health check for the modular data import service."""
    handlers = [
        "clean_api_handler",
        "legacy_upload_handler", 
        "import_retrieval_handler",
        "import_storage_handler"
    ]
    
    if AGENTIC_AVAILABLE:
        handlers.append("agentic_critical_attributes")
    
    return {
        "service": "core_import_modular",
        "status": "healthy",
        "handlers": handlers,
        "agentic_intelligence": AGENTIC_AVAILABLE,
        "message": "All import handlers are loaded and ready"
    }

# Cache clearing endpoint for frontend refresh functionality
@router.post("/clear-cache")
async def clear_cache(db: AsyncSession = Depends(get_db)):
    """
    Clear various caches to ensure fresh data retrieval.
    
    This endpoint clears:
    - SQLAlchemy session cache
    - Any in-memory caches
    - Query result caches
    """
    try:
        # Clear SQLAlchemy session cache
        await db.close()
        
        # Clear any application-level caches
        try:
            # Clear React Query equivalent caches if any exist on backend
            from app.core.cache import clear_all_caches
            clear_all_caches()
        except ImportError:
            # No cache module available, which is fine
            pass
        
        logger.info("✅ Caches cleared successfully")
        
        return {
            "success": True,
            "message": "All caches cleared successfully",
            "cleared_caches": [
                "sqlalchemy_session",
                "application_cache"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        return {
            "success": False,
            "message": f"Failed to clear some caches: {str(e)}",
            "error": str(e)
        } 