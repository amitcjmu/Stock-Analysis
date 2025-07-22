"""
Observability endpoints for monitoring and controlling system behavior.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class PollingControlRequest(BaseModel):
    action: str  # 'stop', 'start', 'status'
    component: str = None
    reason: str = None

# Global polling control state
polling_control = {
    "global_enabled": True,
    "disabled_components": set(),
    "request_counts": {},
}

@router.post("/polling/emergency-stop")
async def emergency_stop_polling() -> Dict[str, Any]:
    """
    Emergency endpoint to immediately stop all polling operations.
    """
    try:
        polling_control["global_enabled"] = False
        polling_control["disabled_components"].clear()
        
        logger.warning("🚨 EMERGENCY STOP: All polling operations halted via API")
        
        return {
            "status": "success",
            "message": "Emergency stop executed - all polling operations halted",
            "timestamp": "now",
            "instructions": [
                "All automatic polling has been stopped",
                "Use manual refresh buttons to update data",
                "Use /api/v1/observability/polling/control with action='resume' to re-enable polling",
                "Check frontend console for 'stopAllPolling()' function"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health including polling status.
    """
    try:
        return {
            "status": "healthy",
            "polling": {
                "global_enabled": polling_control["global_enabled"],
                "disabled_components": list(polling_control["disabled_components"]),
            },
            "recommendations": [
                "Use pull-based requests instead of continuous polling",
                "Implement manual refresh buttons for user-initiated updates",
                "Consider WebSocket connections for real-time updates"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
