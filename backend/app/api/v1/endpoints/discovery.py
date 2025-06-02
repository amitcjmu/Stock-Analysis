"""
Discovery API Endpoints - Modular & Robust
Combines robust error handling with clean modular architecture.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List

from .discovery_handlers.cmdb_analysis import CMDBAnalysisHandler
from .discovery_handlers.data_processing import DataProcessingHandler
from .discovery_handlers.templates import TemplateHandler
from .discovery_handlers.feedback import FeedbackHandler

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Initialize handlers
cmdb_handler = CMDBAnalysisHandler()
processing_handler = DataProcessingHandler()
template_handler = TemplateHandler()
feedback_handler = FeedbackHandler()

# Include asset management router from discovery module
try:
    from app.api.v1.discovery.asset_management import router as asset_management_router
    router.include_router(asset_management_router, tags=["discovery-assets"])
    logger.info("✅ Asset management router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Asset management router not available: {e}")

# Include feedback system router from discovery module
try:
    from app.api.v1.discovery.feedback_system import router as feedback_system_router
    router.include_router(feedback_system_router, tags=["discovery-feedback"])
    logger.info("✅ Feedback system router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Feedback system router not available: {e}")

# Include other discovery routers
try:
    from app.api.v1.discovery.cmdb_analysis import router as cmdb_analysis_router
    router.include_router(cmdb_analysis_router, tags=["discovery-cmdb"])
    logger.info("✅ CMDB analysis router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ CMDB analysis router not available: {e}")

try:
    from app.api.v1.discovery.chat_interface import router as chat_interface_router
    router.include_router(chat_interface_router, tags=["discovery-chat"])
    logger.info("✅ Chat interface router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Chat interface router not available: {e}")

# Include database test router for Railway deployment verification
try:
    from app.api.v1.discovery.database_test import router as database_test_router
    router.include_router(database_test_router, tags=["discovery-database"])
    logger.info("✅ Database test router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Database test router not available: {e}")

# Include data cleanup router for agentic data quality assessment
try:
    from app.api.v1.endpoints.data_cleanup import router as data_cleanup_router
    router.include_router(data_cleanup_router, prefix="/data-cleanup", tags=["discovery-data-cleanup"])
    logger.info("✅ Data cleanup router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Data cleanup router not available: {e}")

# Include agent discovery router for agent status and analysis
try:
    from app.api.v1.endpoints.agent_discovery import router as agent_discovery_router
    router.include_router(agent_discovery_router, prefix="/agents", tags=["discovery-agents"])
    logger.info("✅ Agent discovery router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ Agent discovery router not available: {e}")

# Include app-server mappings router for dependency analysis
try:
    from app.api.v1.discovery.app_server_mappings import router as app_server_mappings_router
    router.include_router(app_server_mappings_router, tags=["discovery-mappings"])
    logger.info("✅ App-server mappings router included in discovery")
except ImportError as e:
    logger.warning(f"⚠️ App-server mappings router not available: {e}")

@router.get("/health")
async def discovery_health_check():
    """Health check endpoint for the discovery module."""
    return {
        "status": "healthy",
        "module": "discovery-modular-robust",
        "version": "3.0.0",
        "components": {
            "cmdb_analysis": cmdb_handler.is_available(),
            "data_processing": processing_handler.is_available(),
            "templates": template_handler.is_available(),
            "feedback": feedback_handler.is_available(),
            "asset_management": True  # Asset management is now included
        },
        "available_endpoints": [
            "/health",
            "/analyze-cmdb",
            "/process-cmdb", 
            "/cmdb-feedback",
            "/cmdb-templates",
            "/feedback",  # General page feedback
            "/assets",  # Asset management endpoints
            "/assets/analyze",
            "/assets/auto-classify",
            "/assets/intelligence-status",
            "/chat-test",  # Chat interface
            "/database/test",  # Database connectivity test
            "/database/health",  # Database health check
            "/data-cleanup/agent-analyze",  # Data cleanup analysis
            "/data-cleanup/agent-process",  # Data cleanup processing
            "/agents/agent-status",  # Agent status endpoint
            "/agents/agent-analysis",  # Agent analysis endpoint
            "/agents/application-portfolio"  # Application portfolio endpoint
        ]
    }

@router.post("/analyze-cmdb")
async def analyze_cmdb_data(request: Dict[str, Any]):
    """
    Robust CMDB analysis endpoint with modular processing.
    """
    try:
        filename = request.get('filename', 'unknown')
        logger.info(f"Analyzing CMDB data for: {filename}")
        
        result = await cmdb_handler.analyze(request)
        return result
        
    except Exception as e:
        logger.error(f"CMDB analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/process-cmdb")
async def process_cmdb_data(request: Dict[str, Any]):
    """
    Robust CMDB processing endpoint.
    """
    try:
        filename = request.get('filename', 'unknown')
        logger.info(f"Processing CMDB data from: {filename}")
        
        result = await processing_handler.process(request)
        return result
        
    except Exception as e:
        logger.error(f"CMDB processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/cmdb-feedback")
async def submit_cmdb_feedback(request: Dict[str, Any]):
    """Submit feedback on CMDB analysis results."""
    try:
        result = await feedback_handler.submit_feedback(request)
        return result
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/cmdb-templates")
async def get_cmdb_templates():
    """Get CMDB template examples and field mappings."""
    try:
        return await template_handler.get_templates()
    except Exception as e:
        logger.error(f"Template retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates") 