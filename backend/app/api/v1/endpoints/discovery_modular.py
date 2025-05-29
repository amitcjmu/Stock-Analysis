"""
Modularized Discovery API Endpoints.
Main router that combines all discovery sub-modules.
"""

import logging
from fastapi import APIRouter

from app.api.v1.discovery import (
    cmdb_analysis_router,
    asset_management_router,
    feedback_system_router,
    app_server_mappings_router,
    testing_endpoints_router,
    chat_interface_router,
    initialize_persistence
)

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(cmdb_analysis_router, tags=["CMDB Analysis"])
router.include_router(asset_management_router, tags=["Asset Management"])
router.include_router(feedback_system_router, tags=["Feedback System"])
router.include_router(app_server_mappings_router, tags=["App-Server Mappings"])
router.include_router(testing_endpoints_router, tags=["Testing & Debug"])
router.include_router(chat_interface_router, tags=["Chat Interface"])

# Initialize persistence on startup
@router.on_event("startup")
async def startup_event():
    """Initialize discovery module on startup."""
    try:
        initialize_persistence()
        logger.info("Discovery module initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize discovery module: {e}")

@router.get("/health")
async def discovery_health_check():
    """Health check endpoint for the discovery module."""
    return {
        "status": "healthy",
        "module": "discovery",
        "version": "2.0.0",
        "modular": True,
        "available_endpoints": {
            "cmdb_analysis": ["/analyze-cmdb", "/process-cmdb", "/cmdb-feedback", "/cmdb-templates"],
            "asset_management": ["/assets", "/applications", "/reprocess-assets"],
            "feedback_system": ["/feedback"],
            "app_server_mappings": ["/app-server-mappings"],
            "testing": ["/test-field-mapping", "/test-asset-classification", "/test-json-parsing", "/ai-parsing-analytics"],
            "chat": ["/chat-test"]
        }
    } 