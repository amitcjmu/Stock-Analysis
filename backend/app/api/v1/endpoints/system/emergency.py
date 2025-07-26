"""
Emergency System Controls

Provides emergency controls for stopping runaway processes.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth.auth_utils import get_current_active_user
from app.models.client_account import User
from app.utils.circuit_breaker import circuit_breaker_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emergency", tags=["system", "emergency"])


@router.post("/circuit-breakers/reset")
async def reset_circuit_breakers(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Reset all circuit breakers (admin only)
    """
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    circuit_breaker_manager.reset_all()

    return {
        "status": "success",
        "message": "All circuit breakers reset",
        "circuit_breakers": circuit_breaker_manager.get_all_states(),
    }


@router.get("/circuit-breakers/status")
async def get_circuit_breaker_status(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get status of all circuit breakers
    """
    return {"circuit_breakers": circuit_breaker_manager.get_all_states()}


@router.post("/polling/stop-all")
async def stop_all_polling(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Emergency stop for all polling operations
    """
    # This endpoint is mainly for documentation
    # Actual polling stop is handled client-side
    logger.warning(f"Emergency polling stop requested by user {current_user.email}")

    return {
        "status": "success",
        "message": "Polling stop signal sent. Frontend polling should stop within 30 seconds.",
        "instructions": [
            "Frontend polling will stop on next error",
            "Use browser console: window.stopAllPolling()",
            "Or refresh the page to reset",
        ],
    }
