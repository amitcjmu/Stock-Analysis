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
            "feedback": feedback_handler.is_available()
        },
        "available_endpoints": [
            "/health",
            "/analyze-cmdb",
            "/process-cmdb", 
            "/cmdb-feedback",
            "/cmdb-templates"
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