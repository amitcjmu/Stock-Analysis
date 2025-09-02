"""
DEPRECATED: Legacy Discovery Endpoints

This module is DEPRECATED and NO LONGER IN USE.
All /api/v1/discovery/* endpoints have been removed from the codebase.

Use instead:
- /api/v1/flows/* for Master Flow Orchestrator operations
- /api/v1/unified-discovery/* for discovery-specific operations

DO NOT import or use any code from this module.
It is retained only for historical reference and will be removed completely.
"""

# Raise an error if anyone tries to import this module
raise ImportError(
    "Legacy discovery endpoints are deprecated and removed. "
    "Use /api/v1/flows/* (MFO) or /api/v1/unified-discovery/* instead."
)
