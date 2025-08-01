"""
Analysis endpoints module.
"""

from fastapi import APIRouter

from .queues import router as queues_router

router = APIRouter()

# Include queues router
router.include_router(queues_router, prefix="/queues", tags=["Analysis Queues"])

__all__ = ["router"]
