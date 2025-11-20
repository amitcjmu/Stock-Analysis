"""
Assessment information endpoints.

Endpoints for retrieving assessment applications, readiness, and progress data.
Enhanced in October 2025 with canonical application support.

This module is modularized into:
- queries.py: GET endpoints for assessment info
- commands.py: PUT endpoints for updating metrics
- schemas.py: Pydantic models for requests/responses

Re-exports router with all endpoints for backward compatibility.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# Import and include all endpoint modules to register routes
from . import queries  # noqa: F401, E402
from . import commands  # noqa: F401, E402

__all__ = ["router"]
