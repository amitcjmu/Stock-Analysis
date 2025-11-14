"""
Assessment lifecycle endpoints.

Endpoints for initializing, resuming, updating, and finalizing assessment flows.

This module is modularized into:
- flow_lifecycle.py: Initialize, resume, finalize endpoints
- data_updates.py: Architecture standards and phase data endpoints
- queries.py: Phase status queries

Re-exports router with all endpoints for backward compatibility.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# Import and include all endpoint modules to register routes
from . import flow_lifecycle  # noqa: F401, E402
from . import data_updates  # noqa: F401, E402
from . import queries  # noqa: F401, E402

__all__ = ["router"]
