"""
Assessment lifecycle endpoints.

DEPRECATED: This file is maintained for backward compatibility only.
All endpoint implementations have been moved to lifecycle_endpoints/ directory.

Endpoints for initializing, resuming, updating, and finalizing assessment flows.

New structure:
- lifecycle_endpoints/__init__.py - Router and imports
- lifecycle_endpoints/flow_lifecycle.py - Initialize, resume, finalize endpoints
- lifecycle_endpoints/data_updates.py - Architecture standards, phase data endpoints
- lifecycle_endpoints/queries.py - Phase status endpoint
"""

# Re-export router from modularized package for backward compatibility
from .lifecycle_endpoints import router

__all__ = ["router"]
