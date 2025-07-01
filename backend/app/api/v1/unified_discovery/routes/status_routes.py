"""
Discovery status and monitoring route handlers.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from ..services.discovery_orchestrator import DiscoveryOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/status", tags=["discovery-status"])


def get_discovery_orchestrator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DiscoveryOrchestrator:
    """Dependency injection for discovery orchestrator."""
    return DiscoveryOrchestrator(db, context)


@router.get("/health", response_model=Dict[str, Any])
async def discovery_health_check():
    """Health check endpoint for discovery system."""
    return {
        "status": "healthy",
        "service": "unified_discovery",
        "layers": {
            "crewai_available": True,  # Would check actual availability
            "database_available": True,
            "handlers_loaded": True
        },
        "api_version": "v1"
    }


@router.get("/assets/{flow_id}", response_model=List[Dict[str, Any]])
async def get_flow_assets(
    flow_id: str,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """Get assets discovered by a specific flow."""
    try:
        # Placeholder implementation
        return [
            {
                "asset_id": "asset_1",
                "name": "Sample Asset",
                "type": "server",
                "status": "discovered"
            }
        ]
    except Exception as e:
        logger.error(f"Failed to get flow assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get flow assets")


@router.get("/assets/{flow_id}/classification-summary", response_model=Dict[str, Any])
async def get_asset_classification_summary(
    flow_id: str,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """Get asset classification summary for a flow."""
    try:
        # Placeholder implementation
        return {
            "flow_id": flow_id,
            "total_assets": 0,
            "by_type": {},
            "classification_confidence": 0.0
        }
    except Exception as e:
        logger.error(f"Failed to get classification summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get classification summary")