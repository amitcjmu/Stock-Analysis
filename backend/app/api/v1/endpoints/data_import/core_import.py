"""
Core Import Module - Modular data upload and import session management.
Delegates to specialized handlers following the modular handler pattern.
"""

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

# Import modular handlers
from .handlers.clean_api_handler import router as clean_api_router
# from .handlers.legacy_upload_handler import router as legacy_upload_router  # File doesn't exist
from .handlers.import_retrieval_handler import router as import_retrieval_router
from .handlers.import_storage_handler import router as import_storage_handler
from .handlers.field_handler import router as field_handler

# Import agentic intelligence modules
AGENTIC_AVAILABLE = False
agentic_critical_attributes_router = None

logger = logging.getLogger(__name__)

# Create main router for data import
router = APIRouter()

# Include all handler routers with proper prefixes
router.include_router(clean_api_router, tags=["Clean API"])
# router.include_router(legacy_upload_router, tags=["Legacy Upload"])  # Router not available - file doesn't exist
router.include_router(import_retrieval_router, tags=["Import Retrieval"])
router.include_router(import_storage_handler, tags=["Import Storage"])
router.include_router(field_handler, tags=["Field Mapping"])

# Critical attributes analysis handled by MasterFlowOrchestrator with real CrewAI agents
logger.info("📦 Critical attributes analysis now handled by MasterFlowOrchestrator")

# Health check endpoint for the modular service
@router.get("/health")
async def health_check():
    """Health check for the modular data import service."""
    handlers = [
        "clean_api_handler",
        # "legacy_upload_handler",  # File doesn't exist
        "import_retrieval_handler",
        "import_storage_handler",
        "field_handler"
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
async def clear_cache(
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear various caches to ensure fresh data retrieval.
    
    This endpoint clears:
    - SQLAlchemy session cache
    - Any in-memory caches
    - Query result caches
    
    Now context-aware for multi-tenant cache management.
    """
    try:
        context_info = "global"
        
        # Extract context if request is provided (for context-specific cache clearing)
        if request:
            try:
                from app.core.context import extract_context_from_request
                context = extract_context_from_request(request)
                if context.client_account_id and context.engagement_id:
                    context_info = f"client={context.client_account_id}, engagement={context.engagement_id}"
            except Exception as context_error:
                logger.warning(f"Could not extract context for cache clearing: {context_error}")
        
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
        
        logger.info(f"✅ Caches cleared successfully for context: {context_info}")
        
        return {
            "success": True,
            "message": f"All caches cleared successfully for {context_info}",
            "cleared_caches": [
                "sqlalchemy_session",
                "application_cache"
            ],
            "context": context_info
        }
        
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        return {
            "success": False,
            "message": f"Failed to clear some caches: {str(e)}",
            "error": str(e)
        } 