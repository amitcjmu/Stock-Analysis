"""
Decommission Flow API Endpoints

This package contains all decommission flow API endpoints following ADR-006 MFO pattern.
"""

from fastapi import APIRouter
from app.api.v1.api_tags import APITags
from .flow_management import router as flow_management_router
from .queries import router as queries_router

# Combine all routers into main router
router = APIRouter()
router.include_router(flow_management_router, tags=[APITags.DECOMMISSION])
router.include_router(queries_router, tags=[APITags.DECOMMISSION])

__all__ = ["router"]
