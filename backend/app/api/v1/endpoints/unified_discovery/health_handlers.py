"""
Health Check Handlers for Unified Discovery

Handles health check endpoints for the unified discovery service.
Extracted from the main unified_discovery.py file for better maintainability.
"""

from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for the unified discovery API."""
    return {
        "status": "healthy",
        "service": "unified_discovery",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "dependency_analysis": "active",
            "agent_insights": "active",
            "flow_management": "active",
            "clarifications": "active",
            "data_extraction": "active",
            "asset_listing": "active",
            "field_mapping": "active",
        },
    }
