"""
Context API Endpoints - Modularized

This file now imports from the modularized context package.
The original 1,447-line file has been split into:

- api/: Route handlers for different context types
- services/: Business logic for context operations
- models/: Pydantic schemas and response models

For backward compatibility, all routes are re-exported through the main router.
"""

# Re-export the main router from the package
from .context import router

# Also export individual components if needed elsewhere
from .context.models.context_schemas import (
    ClientResponse,
    ClientsListResponse,
    EngagementResponse,
    EngagementsListResponse,
    UpdateUserDefaultsRequest,
    UpdateUserDefaultsResponse,
    ValidateContextRequest,
    ValidateContextResponse,
)
from .context.services import ClientService, EngagementService, ValidationService

__all__ = [
    "router",
    # Models
    "ClientResponse",
    "EngagementResponse",
    "ClientsListResponse",
    "EngagementsListResponse",
    "UpdateUserDefaultsRequest",
    "UpdateUserDefaultsResponse",
    "ValidateContextRequest",
    "ValidateContextResponse",
    # Services
    "ClientService",
    "EngagementService",
    "ValidationService",
]
