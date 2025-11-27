"""
Collection Post-Completion Endpoints

Provides API endpoints for resolving unmapped assets to canonical applications
after collection flow completion, enabling seamless transition to Assessment.

This package is a modularized version of the original collection_post_completion.py file,
split into separate files for better maintainability while preserving backward compatibility.

Public API:
    - router: FastAPI router with all endpoints
    - LinkAssetRequest: Pydantic request model
    - UnmappedAssetResponse: Pydantic response model
    - LinkAssetResponse: Pydantic response model
"""

from .endpoints import router
from .schemas import (
    LinkAssetRequest,
    UnmappedAssetResponse,
    LinkAssetResponse,
)

__all__ = [
    "router",
    "LinkAssetRequest",
    "UnmappedAssetResponse",
    "LinkAssetResponse",
]
