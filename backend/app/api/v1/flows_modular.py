"""
Unified Flow API Layer - Modularized Version
Task MFO-059 through MFO-073: Unified API endpoints for all flow types
Provides a single, consistent API for creating, managing, and monitoring all CrewAI flows
"""

import logging

from fastapi import APIRouter

from .flows_handlers.crud_operations import router as crud_router
from .flows_handlers.execution_operations import router as execution_router

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Include modularized routers
router.include_router(crud_router, tags=["Master Flow Coordination"])
router.include_router(execution_router, tags=["Master Flow Coordination"])

logger.info("Modularized flow API routes initialized")
