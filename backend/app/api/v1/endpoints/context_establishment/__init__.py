"""
Context Establishment API - Dedicated endpoints for initial context setup.

These endpoints are designed to work without full engagement context,
allowing the frontend to establish context step by step:
1. Get available clients
2. Get engagements for a specific client
3. Establish full context

These endpoints are exempt from the global engagement requirement middleware.

Modularized Structure:
- models.py: Pydantic response models
- utils.py: Shared utilities and constants
- clients.py: GET /clients endpoint
- engagements.py: GET /engagements endpoint
- user_context.py: POST /update-context endpoint
"""

from fastapi import APIRouter

from app.api.v1.api_tags import APITags

# Import all sub-routers
from .clients import router as clients_router
from .engagements import router as engagements_router
from .user_context import router as user_context_router

# Re-export models for backward compatibility
from .models import (
    ClientResponse,
    ClientsListResponse,
    ContextUpdateRequest,
    ContextUpdateResponse,
    EngagementResponse,
    EngagementsListResponse,
)

# Create main router and include all sub-routers
router = APIRouter()
router.include_router(clients_router, tags=[APITags.CONTEXT_ESTABLISHMENT])
router.include_router(engagements_router, tags=[APITags.CONTEXT_ESTABLISHMENT])
router.include_router(user_context_router, tags=[APITags.CONTEXT_ESTABLISHMENT])

# Export all public interfaces
__all__ = [
    "router",
    "ClientResponse",
    "EngagementResponse",
    "ClientsListResponse",
    "EngagementsListResponse",
    "ContextUpdateRequest",
    "ContextUpdateResponse",
]
