"""
Master Flow Assessment API Endpoints (Backward Compatibility Facade)

This file now serves as a facade to the modularized assessment endpoints.
The actual implementation is in the assessment/ subdirectory.

Modularized October 2025 to comply with 400-line file length limit.
Original file was 742 lines, now split into:
- assessment/helpers.py - Helper functions
- assessment/list_status_endpoints.py - List and status endpoints
- assessment/info_endpoints.py - Applications, readiness, progress endpoints
- assessment/lifecycle_endpoints.py - Initialize, resume, update, finalize endpoints
- assessment/__init__.py - Router aggregation

Import pattern maintains backward compatibility with existing router registry.
"""

# Import the combined router from the modularized package
from .assessment import router

# Export router for router_registry.py compatibility
__all__ = ["router"]
